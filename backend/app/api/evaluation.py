"""过程性评价 API"""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import get_current_user, get_current_teacher, get_current_admin
from app.models.user import User, Class
from app.models.task import Task
from app.models.evaluation import (
    EvalTemplate, EvalPhase, EvalIndicator,
    EvalScorerConfig, EvalRecord, EvalSnapshot
)
from app.models.submission import Submission
from app.models.ai_log import Score, RollcallRecord
from app.schemas.evaluation import (
    TemplateCreate, TemplateUpdate, TemplateResponse, TemplateListResponse,
    PhaseCreate, PhaseUpdate, PhaseResponse,
    IndicatorCreate, IndicatorUpdate, IndicatorResponse,
    ScorerConfigCreate, ScorerConfigResponse,
    RecordCreate, RecordBatchCreate, RecordResponse,
    StudentDashboard, PhaseScoreItem, DimScoreItem,
    StudentTrend, TrendPoint,
    ClassDashboard, ClassDistribution, ClassRankingItem,
    WeightValidation
)

router = APIRouter(prefix="/api/evaluation", tags=["过程性评价"])


# ==================== 权重校验工具 ====================
async def validate_phase_weights(db: AsyncSession, template_id: int) -> WeightValidation:
    """校验模板下所有阶段权重合计是否为100%"""
    result = await db.execute(
        select(func.coalesce(func.sum(EvalPhase.weight), 0))
        .where(EvalPhase.template_id == template_id)
    )
    total = result.scalar() or 0
    return WeightValidation(
        valid=abs(total - 100) < 0.01,
        total_weight=round(total, 2),
        message="权重校验通过" if abs(total - 100) < 0.01 else f"阶段权重合计 {round(total, 2)}%，需为100%"
    )


async def validate_indicator_weights(db: AsyncSession, phase_id: int) -> WeightValidation:
    """校验阶段下所有指标权重合计是否为100%"""
    result = await db.execute(
        select(func.coalesce(func.sum(EvalIndicator.weight), 0))
        .where(EvalIndicator.phase_id == phase_id)
    )
    total = result.scalar() or 0
    return WeightValidation(
        valid=abs(total - 100) < 0.01,
        total_weight=round(total, 2),
        message="权重校验通过" if abs(total - 100) < 0.01 else f"指标权重合计 {round(total, 2)}%，需为100%"
    )


async def validate_scorer_weights(db: AsyncSession, indicator_id: int) -> WeightValidation:
    """校验指标下所有评分主体权重合计是否为100%"""
    result = await db.execute(
        select(func.coalesce(func.sum(EvalScorerConfig.weight), 0))
        .where(EvalScorerConfig.indicator_id == indicator_id)
    )
    total = result.scalar() or 0
    return WeightValidation(
        valid=abs(total - 100) < 0.01,
        total_weight=round(total, 2),
        message="权重校验通过" if abs(total - 100) < 0.01 else f"评分主体权重合计 {round(total, 2)}%，需为100%"
    )


# ==================== 评价方案模板 CRUD ====================
@router.post("/templates")
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """创建评价方案模板"""
    template = EvalTemplate(
        name=data.name,
        description=data.description,
        class_id=data.class_id,
        created_by=current_user.id
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "class_id": template.class_id,
        "is_active": template.is_active,
        "version": template.version,
        "created_by": template.created_by,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "phases": []
    }


@router.get("/templates", response_model=List[TemplateListResponse])
async def list_templates(
    class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取评价方案模板列表"""
    query = select(EvalTemplate)
    if class_id:
        # 返回该班级的模板 + 全局模板（class_id 为 None）
        query = query.where(
            (EvalTemplate.class_id == class_id) | (EvalTemplate.class_id.is_(None))
        )
    query = query.order_by(EvalTemplate.created_at.desc())
    result = await db.execute(query)
    templates = result.scalars().all()

    out = []
    for t in templates:
        # 统计阶段数和指标数
        phase_count_result = await db.execute(
            select(func.count(EvalPhase.id)).where(EvalPhase.template_id == t.id)
        )
        phase_count = phase_count_result.scalar() or 0

        indicator_count_result = await db.execute(
            select(func.count(EvalIndicator.id))
            .join(EvalPhase)
            .where(EvalPhase.template_id == t.id)
        )
        indicator_count = indicator_count_result.scalar() or 0

        out.append(TemplateListResponse(
            id=t.id, name=t.name, description=t.description,
            class_id=t.class_id, is_active=t.is_active, version=t.version,
            phase_count=phase_count, indicator_count=indicator_count,
            created_at=t.created_at
        ))
    return out


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取模板详情（含阶段+指标+评分主体）"""
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template_id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template


@router.put("/templates/{template_id}")
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """更新模板"""
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template_id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(template, field, value)

    await db.commit()
    # 重新查询加载关系
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template_id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    return result.scalar_one()


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除模板"""
    result = await db.execute(select(EvalTemplate).where(EvalTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    await db.delete(template)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/templates/{template_id}/activate")
async def activate_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """激活模板（同类班级只允许一个激活）"""
    result = await db.execute(select(EvalTemplate).where(EvalTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 校验权重
    phase_validation = await validate_phase_weights(db, template_id)
    if not phase_validation.valid:
        raise HTTPException(status_code=400, detail=phase_validation.message)

    # 取消同班级其他激活模板
    if template.class_id:
        others = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.class_id == template.class_id,
                EvalTemplate.id != template_id,
                EvalTemplate.is_active == True
            )
        )
        for t in others.scalars().all():
            t.is_active = False
    else:
        # 全局模板
        others = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.class_id.is_(None),
                EvalTemplate.id != template_id,
                EvalTemplate.is_active == True
            )
        )
        for t in others.scalars().all():
            t.is_active = False

    template.is_active = True
    await db.commit()
    return {"message": "激活成功"}


@router.post("/templates/init-default", response_model=TemplateResponse)
async def init_default_template(
    class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """初始化默认评价模板（课前10%+课中35%+课后10%）"""
    template = EvalTemplate(
        name="默认过程性评价方案",
        description="基于教学实施报告的默认评价体系，包含课前/课中/课后三阶段",
        class_id=class_id,
        created_by=current_user.id
    )
    db.add(template)
    await db.flush()

    # 课前阶段
    phase_pre = EvalPhase(template_id=template.id, name="课前", weight=10, sort_order=1)
    db.add(phase_pre)
    await db.flush()

    indicators_pre = [
        EvalIndicator(phase_id=phase_pre.id, name="线上预练", weight=50, capability_dim="knowledge", data_source="manual", sort_order=1),
        EvalIndicator(phase_id=phase_pre.id, name="教学平台学习", weight=30, capability_dim="knowledge", data_source="manual", sort_order=2),
        EvalIndicator(phase_id=phase_pre.id, name="出勤", weight=20, capability_dim="quality", data_source="attendance", auto_collect=True, sort_order=3),
    ]
    db.add_all(indicators_pre)

    # 课中阶段
    phase_mid = EvalPhase(template_id=template.id, name="课中", weight=35, sort_order=2)
    db.add(phase_mid)
    await db.flush()

    indicators_mid = [
        EvalIndicator(phase_id=phase_mid.id, name="软件仿练", weight=15, capability_dim="skill", data_source="submission", auto_collect=True, sort_order=1),
        EvalIndicator(phase_id=phase_mid.id, name="数智模考", weight=30, capability_dim="knowledge", data_source="ai_score", auto_collect=True, sort_order=2),
        EvalIndicator(phase_id=phase_mid.id, name="真人实践", weight=55, capability_dim="skill", data_source="submission", auto_collect=True, sort_order=3),
    ]
    db.add_all(indicators_mid)

    # 课后阶段
    phase_post = EvalPhase(template_id=template.id, name="课后", weight=10, sort_order=3)
    db.add(phase_post)
    await db.flush()

    indicators_post = [
        EvalIndicator(phase_id=phase_post.id, name="社区/项目真练", weight=50, capability_dim="innovation", data_source="manual", sort_order=1),
        EvalIndicator(phase_id=phase_post.id, name="答辩竞展", weight=50, capability_dim="quality", data_source="manual", sort_order=2),
    ]
    db.add_all(indicators_post)

    await db.commit()

    # 重新查询以加载关系
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template.id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    return result.scalar_one()


# ==================== 评价阶段 CRUD ====================
@router.post("/templates/{template_id}/phases")
async def create_phase(
    template_id: int,
    data: PhaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """添加评价阶段"""
    # 检查模板存在
    result = await db.execute(select(EvalTemplate).where(EvalTemplate.id == template_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="模板不存在")

    phase = EvalPhase(
        template_id=template_id,
        name=data.name,
        weight=data.weight,
        sort_order=data.sort_order
    )
    db.add(phase)
    await db.commit()
    await db.refresh(phase)
    return {"id": phase.id, "template_id": phase.template_id, "name": phase.name, "weight": phase.weight, "sort_order": phase.sort_order, "indicators": []}


@router.put("/phases/{phase_id}")
async def update_phase(
    phase_id: int,
    data: PhaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """更新阶段"""
    result = await db.execute(
        select(EvalPhase)
        .where(EvalPhase.id == phase_id)
        .options(selectinload(EvalPhase.indicators).selectinload(EvalIndicator.scorer_configs))
    )
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(phase, field, value)

    await db.commit()
    result = await db.execute(
        select(EvalPhase)
        .where(EvalPhase.id == phase_id)
        .options(selectinload(EvalPhase.indicators).selectinload(EvalIndicator.scorer_configs))
    )
    return result.scalar_one()


@router.delete("/phases/{phase_id}")
async def delete_phase(
    phase_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除阶段"""
    result = await db.execute(select(EvalPhase).where(EvalPhase.id == phase_id))
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    await db.delete(phase)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/templates/{template_id}/weight-validation", response_model=WeightValidation)
async def check_template_weights(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """校验模板权重"""
    return await validate_phase_weights(db, template_id)


# ==================== 评价指标 CRUD ====================
@router.post("/phases/{phase_id}/indicators")
async def create_indicator(
    phase_id: int,
    data: IndicatorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """添加评价指标"""
    result = await db.execute(select(EvalPhase).where(EvalPhase.id == phase_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="阶段不存在")

    indicator = EvalIndicator(
        phase_id=phase_id,
        name=data.name,
        weight=data.weight,
        max_score=data.max_score,
        score_type=data.score_type,
        capability_dim=data.capability_dim,
        data_source=data.data_source,
        auto_collect=data.auto_collect,
        sort_order=data.sort_order
    )
    db.add(indicator)
    await db.flush()

    # 添加评分主体配置
    if data.scorer_configs:
        for sc in data.scorer_configs:
            scorer = EvalScorerConfig(
                indicator_id=indicator.id,
                scorer_role=sc.scorer_role,
                weight=sc.weight
            )
            db.add(scorer)

    await db.commit()
    await db.refresh(indicator)

    # 重新查询加载关系
    result = await db.execute(
        select(EvalIndicator)
        .where(EvalIndicator.id == indicator.id)
        .options(selectinload(EvalIndicator.scorer_configs))
    )
    return result.scalar_one()


@router.put("/indicators/{indicator_id}")
async def update_indicator(
    indicator_id: int,
    data: IndicatorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """更新指标"""
    result = await db.execute(
        select(EvalIndicator)
        .where(EvalIndicator.id == indicator_id)
        .options(selectinload(EvalIndicator.scorer_configs))
    )
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(indicator, field, value)

    await db.commit()
    await db.refresh(indicator)

    result = await db.execute(
        select(EvalIndicator)
        .where(EvalIndicator.id == indicator_id)
        .options(selectinload(EvalIndicator.scorer_configs))
    )
    return result.scalar_one()


@router.delete("/indicators/{indicator_id}")
async def delete_indicator(
    indicator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除指标"""
    result = await db.execute(select(EvalIndicator).where(EvalIndicator.id == indicator_id))
    indicator = result.scalar_one_or_none()
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    await db.delete(indicator)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/phases/{phase_id}/indicators/weight-validation", response_model=WeightValidation)
async def check_indicator_weights(
    phase_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """校验阶段内指标权重"""
    return await validate_indicator_weights(db, phase_id)


# ==================== 评分主体配置 ====================
@router.post("/indicators/{indicator_id}/scorers", response_model=ScorerConfigResponse)
async def add_scorer_config(
    indicator_id: int,
    data: ScorerConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """添加评分主体配置"""
    result = await db.execute(select(EvalIndicator).where(EvalIndicator.id == indicator_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="指标不存在")

    scorer = EvalScorerConfig(
        indicator_id=indicator_id,
        scorer_role=data.scorer_role,
        weight=data.weight
    )
    db.add(scorer)
    await db.commit()
    await db.refresh(scorer)
    return scorer


@router.delete("/scorers/{scorer_id}")
async def delete_scorer_config(
    scorer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除评分主体配置"""
    result = await db.execute(select(EvalScorerConfig).where(EvalScorerConfig.id == scorer_id))
    scorer = result.scalar_one_or_none()
    if not scorer:
        raise HTTPException(status_code=404, detail="评分主体配置不存在")

    await db.delete(scorer)
    await db.commit()
    return {"message": "删除成功"}


# ==================== 评价记录 ====================
@router.post("/records", response_model=RecordResponse)
async def create_record(
    data: RecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """单条录入评价记录"""
    record = EvalRecord(
        student_id=data.student_id,
        indicator_id=data.indicator_id,
        template_id=data.template_id,
        score=data.score,
        scorer_id=current_user.id,
        scorer_role=data.scorer_role,
        evidence_type=data.evidence_type,
        evidence_id=data.evidence_id,
        remark=data.remark
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    # 填充关联信息
    response = RecordResponse.model_validate(record)
    student = await db.get(User, record.student_id)
    if student:
        response.student_name = student.name or student.username
    indicator = await db.get(EvalIndicator, record.indicator_id)
    if indicator:
        response.indicator_name = indicator.name
        phase = await db.get(EvalPhase, indicator.phase_id)
        if phase:
            response.phase_name = phase.name

    return response


@router.post("/records/batch")
async def batch_create_records(
    data: RecordBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """批量录入评价记录"""
    records = []
    for r in data.records:
        record = EvalRecord(
            student_id=r.get("student_id"),
            indicator_id=data.indicator_id,
            template_id=data.template_id,
            score=r.get("score"),
            scorer_id=current_user.id,
            scorer_role="teacher",
            evidence_type="manual",
            remark=r.get("remark")
        )
        db.add(record)
        records.append(record)

    await db.commit()
    return {"message": f"成功录入 {len(records)} 条记录", "count": len(records)}


@router.get("/records", response_model=List[RecordResponse])
async def list_records(
    template_id: Optional[int] = None,
    student_id: Optional[int] = None,
    indicator_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """查询评价记录"""
    query = select(EvalRecord)
    if template_id:
        query = query.where(EvalRecord.template_id == template_id)
    if student_id:
        query = query.where(EvalRecord.student_id == student_id)
    if indicator_id:
        query = query.where(EvalRecord.indicator_id == indicator_id)
    query = query.order_by(EvalRecord.created_at.desc())

    result = await db.execute(query)
    records = result.scalars().all()

    out = []
    for record in records:
        resp = RecordResponse.model_validate(record)
        student = await db.get(User, record.student_id)
        if student:
            resp.student_name = student.name or student.username
        indicator = await db.get(EvalIndicator, record.indicator_id)
        if indicator:
            resp.indicator_name = indicator.name
            phase = await db.get(EvalPhase, indicator.phase_id)
            if phase:
                resp.phase_name = phase.name
        out.append(resp)

    return out


# ==================== 学生自评/互评 ====================
@router.post("/records/self-eval")
async def student_self_eval(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生自评 — 学生给自己打分"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可使用自评功能")

    indicator_id = data.get("indicator_id")
    template_id = data.get("template_id")
    score = data.get("score")
    remark = data.get("remark", "")

    if not indicator_id or not template_id or score is None:
        raise HTTPException(status_code=400, detail="请提供 indicator_id、template_id 和 score")

    # 验证指标存在且配置了 self 评分主体
    indicator = await db.get(EvalIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    has_self = any(
        sc.scorer_role == "self"
        for sc in (indicator.scorer_configs or [])
    )
    if not has_self:
        raise HTTPException(status_code=400, detail="该指标未配置学生自评")

    record = EvalRecord(
        student_id=current_user.id,
        indicator_id=indicator_id,
        template_id=template_id,
        score=score,
        scorer_id=current_user.id,
        scorer_role="self",
        evidence_type="self_eval",
        remark=remark
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"message": "自评提交成功", "record_id": record.id}


@router.post("/records/peer-eval")
async def student_peer_eval(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生互评 — 学生给同班同学打分"""
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="仅学生可使用互评功能")

    indicator_id = data.get("indicator_id")
    template_id = data.get("template_id")
    target_student_id = data.get("student_id")
    score = data.get("score")
    remark = data.get("remark", "")

    if not indicator_id or not template_id or not target_student_id or score is None:
        raise HTTPException(status_code=400, detail="请提供完整参数")

    # 不能给自己互评
    if target_student_id == current_user.id:
        raise HTTPException(status_code=400, detail="互评不能给自己打分，请使用自评功能")

    # 验证指标配置了 peer 评分主体
    indicator = await db.get(EvalIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    has_peer = any(
        sc.scorer_role == "peer"
        for sc in (indicator.scorer_configs or [])
    )
    if not has_peer:
        raise HTTPException(status_code=400, detail="该指标未配置学生互评")

    # 验证被评学生与当前用户同班
    target = await db.get(User, target_student_id)
    if not target or target.role != "student":
        raise HTTPException(status_code=404, detail="目标学生不存在")
    if target.class_id != current_user.class_id:
        raise HTTPException(status_code=403, detail="只能评价同班同学")

    record = EvalRecord(
        student_id=target_student_id,
        indicator_id=indicator_id,
        template_id=template_id,
        score=score,
        scorer_id=current_user.id,
        scorer_role="peer",
        evidence_type="peer_eval",
        remark=remark
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return {"message": "互评提交成功", "record_id": record.id}


@router.get("/indicators/{indicator_id}/students")
async def get_indicator_students(
    indicator_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指标对应班级的所有学生及其评分记录"""
    indicator = await db.get(EvalIndicator, indicator_id)
    if not indicator:
        raise HTTPException(status_code=404, detail="指标不存在")

    # 获取阶段和模板
    phase = await db.get(EvalPhase, indicator.phase_id)
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")
    template = await db.get(EvalTemplate, phase.template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取目标学生
    student_query = select(User).where(User.role == "student")
    if current_user.role == "student":
        # 学生只能看同班同学
        student_query = student_query.where(User.class_id == current_user.class_id)
    elif template.class_id:
        student_query = student_query.where(User.class_id == template.class_id)
    students_result = await db.execute(student_query.order_by(User.id))
    students = students_result.scalars().all()

    # 获取每个学生的最新评分记录
    result = []
    for student in students:
        record_result = await db.execute(
            select(EvalRecord)
            .where(
                EvalRecord.student_id == student.id,
                EvalRecord.indicator_id == indicator_id,
                EvalRecord.template_id == template.id
            )
            .order_by(EvalRecord.created_at.desc())
            .limit(1)
        )
        latest_record = record_result.scalar_one_or_none()
        result.append({
            "student_id": student.id,
            "student_name": student.name or student.username,
            "username": student.username,
            "class_id": student.class_id,
            "latest_score": latest_record.score if latest_record else None,
            "latest_scorer_role": latest_record.scorer_role if latest_record else None,
            "latest_remark": latest_record.remark if latest_record else None,
            "latest_record_id": latest_record.id if latest_record else None,
        })

    return {
        "indicator_id": indicator_id,
        "indicator_name": indicator.name,
        "template_id": template.id,
        "template_name": template.name,
        "scorer_configs": [
            {"scorer_role": sc.scorer_role, "weight": sc.weight}
            for sc in (indicator.scorer_configs or [])
        ],
        "students": result
    }


# ==================== 自动采集 ====================
@router.post("/records/auto-collect/{template_id}")
async def auto_collect(
    template_id: int,
    class_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """触发自动采集（从提交/AI评分/出勤拉取数据）"""
    # 获取模板及所有自动采集指标
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template_id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 获取目标学生
    student_query = select(User).where(User.role == "student")
    if class_id:
        student_query = student_query.where(User.class_id == class_id)
    elif template.class_id:
        student_query = student_query.where(User.class_id == template.class_id)
    students_result = await db.execute(student_query)
    students = students_result.scalars().all()

    collected_count = 0

    for student in students:
        for phase in template.phases:
            for indicator in phase.indicators:
                if not indicator.auto_collect:
                    continue

                # 检查是否已有该指标的最新记录
                existing = await db.execute(
                    select(EvalRecord).where(
                        EvalRecord.student_id == student.id,
                        EvalRecord.indicator_id == indicator.id,
                        EvalRecord.template_id == template_id
                    ).order_by(EvalRecord.created_at.desc()).limit(1)
                )
                # 如果最近24小时内已有记录则跳过
                recent = existing.scalar_one_or_none()
                if recent and recent.created_at and (datetime.utcnow() - recent.created_at).total_seconds() < 86400:
                    continue

                score = None
                evidence_type = None
                evidence_id = None

                if indicator.data_source == "submission":
                    # 从提交记录采集：计算该学生在所有任务的平均完成分
                    sub_result = await db.execute(
                        select(func.avg(Submission.final_score))
                        .where(Submission.user_id == student.id, Submission.final_score.isnot(None))
                    )
                    avg_score = sub_result.scalar()
                    if avg_score is not None:
                        score = round(avg_score, 1)
                        evidence_type = "submission"

                elif indicator.data_source == "ai_score":
                    # 从 AI 评分采集
                    score_result = await db.execute(
                        select(func.avg(Score.ai_total_score))
                        .where(Score.user_id == student.id, Score.ai_total_score.isnot(None))
                    )
                    avg_score = score_result.scalar()
                    if avg_score is not None:
                        score = round(avg_score, 1)
                        evidence_type = "ai_score"

                elif indicator.data_source == "attendance":
                    # 从出勤记录采集
                    rollcall_result = await db.execute(
                        select(func.count(RollcallRecord.id))
                        .where(RollcallRecord.student_id == student.id)
                    )
                    count = rollcall_result.scalar() or 0
                    # 出勤分 = min(100, 出勤次数 * 10)
                    score = min(100.0, count * 10.0)
                    evidence_type = "attendance"

                elif indicator.data_source == "task_score":
                    # 从教学任务综合分采集 (Score.final_score = AI*权重 + 教师*权重)
                    task_score_result = await db.execute(
                        select(func.avg(Score.final_score))
                        .where(Score.user_id == student.id, Score.final_score.isnot(None))
                    )
                    avg_score = task_score_result.scalar()
                    if avg_score is not None:
                        score = round(avg_score, 1)
                        evidence_type = "task_score"

                if score is not None:
                    # 根据数据源和评分主体配置确定 scorer_role
                    scorer_role = "system"
                    data_source_role_map = {
                        "ai_score": "ai",
                        "submission": "teacher",
                        "attendance": "teacher",
                        "task_score": "teacher",
                    }
                    candidate_role = data_source_role_map.get(indicator.data_source)
                    if candidate_role and any(
                        sc.scorer_role == candidate_role
                        for sc in (indicator.scorer_configs or [])
                    ):
                        scorer_role = candidate_role

                    record = EvalRecord(
                        student_id=student.id,
                        indicator_id=indicator.id,
                        template_id=template_id,
                        score=score,
                        scorer_role=scorer_role,
                        evidence_type=evidence_type,
                        evidence_id=evidence_id
                    )
                    db.add(record)
                    collected_count += 1

    await db.commit()
    return {"message": f"自动采集完成，共采集 {collected_count} 条记录", "count": collected_count}


# ==================== 计算引擎 ====================
async def calculate_student_score(
    db: AsyncSession,
    student_id: int,
    template_id: int
) -> dict:
    """计算学生的过程性评价总分及各维度得分"""
    # 获取模板结构
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template_id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    template = result.scalar_one_or_none()
    if not template:
        return None

    phase_scores = []
    dim_scores_map = {
        "knowledge": [], "skill": [], "quality": [], "innovation": []
    }
    total_score = 0

    for phase in template.phases:
        phase_total = 0
        phase_weight_sum = 0
        indicator_details = []

        for indicator in phase.indicators:
            # 获取该指标的所有评价记录
            records_result = await db.execute(
                select(EvalRecord).where(
                    EvalRecord.student_id == student_id,
                    EvalRecord.indicator_id == indicator.id,
                    EvalRecord.template_id == template_id
                )
            )
            records = records_result.scalars().all()

            if records:
                # 如果有多个评分主体，按配置权重加权平均
                if indicator.scorer_configs:
                    weighted_sum = 0
                    weight_total = 0
                    for sc in indicator.scorer_configs:
                        role_records = [r for r in records if r.scorer_role == sc.scorer_role]
                        if role_records:
                            avg = sum(r.score or 0 for r in role_records) / len(role_records)
                            weighted_sum += avg * sc.weight
                            weight_total += sc.weight
                    indicator_score = weighted_sum / weight_total if weight_total > 0 else 0
                else:
                    # 无主体配置，取所有记录平均值
                    indicator_score = sum(r.score or 0 for r in records) / len(records)
            else:
                indicator_score = 0

            # 标准化到满分
            normalized = (indicator_score / indicator.max_score * 100) if indicator.max_score > 0 else 0
            phase_total += normalized * (indicator.weight / 100)
            phase_weight_sum += indicator.weight

            indicator_details.append({
                "id": indicator.id,
                "name": indicator.name,
                "score": round(indicator_score, 1),
                "max_score": indicator.max_score,
                "weight": indicator.weight,
                "normalized_score": round(normalized, 1)
            })

            # 按能力维度汇总
            dim_scores_map[indicator.capability_dim].append(normalized)

        phase_score = phase_total
        weighted_phase = phase_score * (phase.weight / 100)
        total_score += weighted_phase

        phase_scores.append(PhaseScoreItem(
            phase_id=phase.id,
            phase_name=phase.name,
            phase_weight=phase.weight,
            score=round(phase_score, 1),
            weighted_score=round(weighted_phase, 1),
            indicators=indicator_details
        ))

    # 计算四维能力分
    dim_labels = {
        "knowledge": "知识基础", "skill": "工法能力",
        "quality": "职业素养", "innovation": "创新贡献"
    }
    dim_score_items = []
    for dim, scores in dim_scores_map.items():
        avg = sum(scores) / len(scores) if scores else 0
        dim_score_items.append(DimScoreItem(
            dimension=dim,
            dim_label=dim_labels[dim],
            score=round(avg, 1),
            count=len(scores)
        ))

    return {
        "total_score": round(total_score, 1),
        "phase_scores": phase_scores,
        "dim_scores": dim_score_items
    }


# ==================== 看板 API ====================
@router.get("/dashboard/student/{student_id}")
async def get_student_dashboard(
    student_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生个人看板数据"""
    # 权限检查：学生只能看自己，教师可以看所有
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="权限不足")

    # 成绩可见性检查
    from app.api.auth import _system_settings
    if current_user.role == "student" and not _system_settings.get("student_view_grades", True):
        raise HTTPException(status_code=403, detail="成绩暂未开放查看")

    # 获取活跃模板
    if not template_id:
        student = await db.get(User, student_id)
        if not student:
            raise HTTPException(status_code=404, detail="学生不存在")

        result = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.is_active == True,
                (EvalTemplate.class_id == student.class_id) | (EvalTemplate.class_id.is_(None))
            ).order_by(EvalTemplate.class_id.desc()).limit(1)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="没有激活的评价方案")
        template_id = template.id
    else:
        template = await db.get(EvalTemplate, template_id)

    calc_result = await calculate_student_score(db, student_id, template_id)
    if not calc_result:
        raise HTTPException(status_code=404, detail="计算失败")

    student = await db.get(User, student_id)

    # 保存快照
    snapshot = EvalSnapshot(
        student_id=student_id,
        template_id=template_id,
        total_score=calc_result["total_score"],
        phase_scores=json.dumps({p.phase_name: p.score for p in calc_result["phase_scores"]}),
        dim_scores=json.dumps({d.dimension: d.score for d in calc_result["dim_scores"]})
    )
    db.add(snapshot)
    await db.commit()

    return StudentDashboard(
        student_id=student_id,
        student_name=student.name or student.username,
        template_id=template_id,
        template_name=template.name,
        total_score=calc_result["total_score"],
        phase_scores=calc_result["phase_scores"],
        dim_scores=calc_result["dim_scores"],
        snapshot_date=snapshot.snapshot_date
    )


@router.get("/dashboard/student/{student_id}/radar")
async def get_student_radar(
    student_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """四维雷达图数据"""
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="权限不足")

    from app.api.auth import _system_settings
    if current_user.role == "student" and not _system_settings.get("student_view_grades", True):
        raise HTTPException(status_code=403, detail="成绩暂未开放查看")

    if not template_id:
        student = await db.get(User, student_id)
        result = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.is_active == True,
                (EvalTemplate.class_id == student.class_id) | (EvalTemplate.class_id.is_(None))
            ).order_by(EvalTemplate.class_id.desc()).limit(1)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="没有激活的评价方案")
        template_id = template.id

    calc_result = await calculate_student_score(db, student_id, template_id)
    if not calc_result:
        raise HTTPException(status_code=404, detail="计算失败")

    return calc_result["dim_scores"]


@router.get("/dashboard/student/{student_id}/trend")
async def get_student_trend(
    student_id: int,
    template_id: Optional[int] = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """成长趋势数据"""
    if current_user.role == "student" and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="权限不足")

    from app.api.auth import _system_settings
    if current_user.role == "student" and not _system_settings.get("student_view_grades", True):
        raise HTTPException(status_code=403, detail="成绩暂未开放查看")

    if not template_id:
        student = await db.get(User, student_id)
        result = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.is_active == True,
                (EvalTemplate.class_id == student.class_id) | (EvalTemplate.class_id.is_(None))
            ).order_by(EvalTemplate.class_id.desc()).limit(1)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="没有激活的评价方案")
        template_id = template.id

    result = await db.execute(
        select(EvalSnapshot)
        .where(EvalSnapshot.student_id == student_id, EvalSnapshot.template_id == template_id)
        .order_by(EvalSnapshot.snapshot_date.asc())
        .limit(limit)
    )
    snapshots = result.scalars().all()

    points = []
    for s in snapshots:
        points.append(TrendPoint(
            date=s.snapshot_date.strftime("%Y-%m-%d") if s.snapshot_date else "",
            total_score=s.total_score or 0,
            phase_scores=json.loads(s.phase_scores) if s.phase_scores else {},
            dim_scores=json.loads(s.dim_scores) if s.dim_scores else {}
        ))

    return StudentTrend(student_id=student_id, points=points)


@router.get("/dashboard/class/{class_id}")
async def get_class_dashboard(
    class_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """班级看板数据"""
    # 获取班级信息
    class_obj = await db.get(Class, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 获取活跃模板
    if not template_id:
        result = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.is_active == True,
                (EvalTemplate.class_id == class_id) | (EvalTemplate.class_id.is_(None))
            ).order_by(EvalTemplate.class_id.desc()).limit(1)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="没有激活的评价方案")
        template_id = template.id

    # 获取班级学生
    students_result = await db.execute(
        select(User).where(User.class_id == class_id, User.role == "student")
    )
    students = students_result.scalars().all()

    # 计算每个学生的总分
    student_scores = []
    for student in students:
        calc = await calculate_student_score(db, student.id, template_id)
        if calc:
            student_scores.append({
                "student_id": student.id,
                "student_name": student.name or student.username,
                "total_score": calc["total_score"],
                "dim_scores": calc["dim_scores"]
            })

    # 分布统计
    score_ranges = [
        {"range": "90-100", "count": 0},
        {"range": "80-89", "count": 0},
        {"range": "70-79", "count": 0},
        {"range": "60-69", "count": 0},
        {"range": "0-59", "count": 0},
    ]
    for s in student_scores:
        score = s["total_score"]
        if score >= 90:
            score_ranges[0]["count"] += 1
        elif score >= 80:
            score_ranges[1]["count"] += 1
        elif score >= 70:
            score_ranges[2]["count"] += 1
        elif score >= 60:
            score_ranges[3]["count"] += 1
        else:
            score_ranges[4]["count"] += 1

    total = len(student_scores)
    avg_score = sum(s["total_score"] for s in student_scores) / total if total > 0 else 0
    pass_count = sum(1 for s in student_scores if s["total_score"] >= 60)
    excellent_count = sum(1 for s in student_scores if s["total_score"] >= 90)

    distribution = ClassDistribution(
        score_ranges=score_ranges,
        total_students=total,
        average_score=round(avg_score, 1),
        pass_rate=round(pass_count / total * 100, 1) if total > 0 else 0,
        excellent_rate=round(excellent_count / total * 100, 1) if total > 0 else 0
    )

    # 排行榜
    sorted_students = sorted(student_scores, key=lambda x: x["total_score"], reverse=True)
    ranking = []
    for i, s in enumerate(sorted_students):
        ranking.append(ClassRankingItem(
            rank=i + 1,
            student_id=s["student_id"],
            student_name=s["student_name"],
            total_score=s["total_score"]
        ))

    # 共性短板
    dim_totals = {"knowledge": [], "skill": [], "quality": [], "innovation": []}
    dim_labels = {
        "knowledge": "知识基础", "skill": "工法能力",
        "quality": "职业素养", "innovation": "创新贡献"
    }
    for s in student_scores:
        for d in s["dim_scores"]:
            dim_totals[d.dimension].append(d.score)

    weak_dims = []
    for dim, scores in dim_totals.items():
        avg = sum(scores) / len(scores) if scores else 0
        weak_dims.append({"dimension": dim, "label": dim_labels[dim], "avg_score": round(avg, 1)})
    weak_dims.sort(key=lambda x: x["avg_score"])

    return ClassDashboard(
        class_id=class_id,
        class_name=class_obj.name,
        template_id=template_id,
        distribution=distribution,
        ranking=ranking[:20],
        weak_dims=weak_dims
    )


@router.get("/dashboard/class/{class_id}/ranking")
async def get_class_ranking(
    class_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """班级排行榜"""
    # 复用 class dashboard 的逻辑
    dashboard = await get_class_dashboard(class_id, template_id, db, current_user)
    return dashboard.ranking


# ==================== AI 辅助配置 ====================
@router.post("/ai/generate-template")
async def ai_generate_template(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """AI 生成评价方案模板"""
    from app.services.ai_service import ai_service

    course_name = data.get("course_name", "")
    course_description = data.get("course_description", "")
    category = data.get("category", "")
    student_count = data.get("student_count", 0)
    task_count = data.get("task_count", 0)

    if not course_name:
        raise HTTPException(status_code=400, detail="请提供课程名称")

    result = await ai_service.generate_eval_template(
        course_name=course_name,
        course_description=course_description,
        category=category,
        student_count=student_count,
        task_count=task_count
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    # 将 AI 生成的方案直接创建为模板
    template_data = result["data"]
    template = EvalTemplate(
        name=template_data.get("name", f"{course_name}过程性评价方案"),
        description=template_data.get("description", ""),
        class_id=data.get("class_id"),
        created_by=current_user.id
    )
    db.add(template)
    await db.flush()

    for phase_data in template_data.get("phases", []):
        phase = EvalPhase(
            template_id=template.id,
            name=phase_data["name"],
            weight=phase_data.get("weight", 0),
            sort_order=phase_data.get("sort_order", 0)
        )
        db.add(phase)
        await db.flush()

        for ind_data in phase_data.get("indicators", []):
            indicator = EvalIndicator(
                phase_id=phase.id,
                name=ind_data["name"],
                weight=ind_data.get("weight", 0),
                max_score=ind_data.get("max_score", 100),
                score_type=ind_data.get("score_type", "value"),
                capability_dim=ind_data.get("capability_dim", "knowledge"),
                data_source=ind_data.get("data_source", "manual"),
                auto_collect=ind_data.get("auto_collect", False),
                sort_order=ind_data.get("sort_order", 0)
            )
            db.add(indicator)
            await db.flush()

            for sc_data in ind_data.get("scorer_configs", []):
                scorer = EvalScorerConfig(
                    indicator_id=indicator.id,
                    scorer_role=sc_data["scorer_role"],
                    weight=sc_data.get("weight", 100)
                )
                db.add(scorer)

    await db.commit()

    # 返回完整模板
    result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == template.id)
        .options(
            selectinload(EvalTemplate.phases)
            .selectinload(EvalPhase.indicators)
            .selectinload(EvalIndicator.scorer_configs)
        )
    )
    return result.scalar_one()


@router.post("/ai/suggest-indicators")
async def ai_suggest_indicators(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """AI 推荐评价指标"""
    from app.services.ai_service import ai_service

    phase_id = data.get("phase_id")
    if not phase_id:
        raise HTTPException(status_code=400, detail="请提供阶段 ID")

    # 获取阶段信息
    result = await db.execute(
        select(EvalPhase)
        .where(EvalPhase.id == phase_id)
        .options(selectinload(EvalPhase.indicators))
    )
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="阶段不存在")

    # 获取模板信息
    template_result = await db.execute(
        select(EvalTemplate)
        .where(EvalTemplate.id == phase.template_id)
        .options(selectinload(EvalTemplate.phases).selectinload(EvalPhase.indicators))
    )
    template = template_result.scalar_one()

    existing = [f"{i.name}(权重{i.weight}%)" for i in phase.indicators]
    other_phases = [f"{p.name}(权重{p.weight}%)" for p in template.phases if p.id != phase_id]

    # 获取课程分类
    class_id = template.class_id
    category = ""
    if class_id:
        tasks_result = await db.execute(
            select(Task.category).distinct().limit(1)
        )
        cat = tasks_result.scalar_one_or_none()
        if cat:
            category = cat

    result = await ai_service.suggest_indicators(
        phase_name=phase.name,
        phase_weight=phase.weight,
        existing_indicators=", ".join(existing) if existing else "",
        category=category,
        other_phases=", ".join(other_phases) if other_phases else ""
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return {"indicators": result["data"], "tokens_used": result["tokens_used"]}


@router.post("/ai/diagnose/{student_id}")
async def ai_diagnose_student(
    student_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """AI 学生个体诊断"""
    from app.services.ai_service import ai_service

    student = await db.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 获取班级名
    class_name = ""
    if student.class_id:
        class_obj = await db.get(Class, student.class_id)
        class_name = class_obj.name if class_obj else ""

    # 获取活跃模板
    if not template_id:
        result = await db.execute(
            select(EvalTemplate).where(
                EvalTemplate.is_active == True,
                (EvalTemplate.class_id == student.class_id) | (EvalTemplate.class_id.is_(None))
            ).order_by(EvalTemplate.class_id.desc()).limit(1)
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(status_code=404, detail="没有激活的评价方案")
        template_id = template.id
    else:
        template = await db.get(EvalTemplate, template_id)

    # 计算学生分数
    calc = await calculate_student_score(db, student_id, template_id)
    if not calc:
        raise HTTPException(status_code=404, detail="计算失败")

    # 格式化阶段详情
    phase_lines = []
    for p in calc["phase_scores"]:
        indicators_str = ", ".join([f"{i['name']}:{i['score']}" for i in p.indicators])
        phase_lines.append(f"- {p.phase_name}(权重{p.phase_weight}%): {p.score}分 [{indicators_str}]")
    phase_details = "\n".join(phase_lines)

    # 格式化维度详情
    dim_lines = [f"- {d.dim_label}: {d.score}分" for d in calc["dim_scores"]]
    dim_details = "\n".join(dim_lines)

    # 获取趋势数据
    trend_result = await db.execute(
        select(EvalSnapshot)
        .where(EvalSnapshot.student_id == student_id, EvalSnapshot.template_id == template_id)
        .order_by(EvalSnapshot.snapshot_date.desc())
        .limit(5)
    )
    snapshots = trend_result.scalars().all()
    trend_lines = []
    for s in reversed(snapshots):
        date_str = s.snapshot_date.strftime("%Y-%m-%d") if s.snapshot_date else "未知"
        trend_lines.append(f"- {date_str}: 总分{s.total_score}")
    trend_data = "\n".join(trend_lines) if trend_lines else ""

    result = await ai_service.diagnose_student(
        student_name=student.name or student.username,
        class_name=class_name,
        template_name=template.name,
        total_score=calc["total_score"],
        phase_details=phase_details,
        dim_details=dim_details,
        trend_data=trend_data
    )

    return {"report": result["report"], "tokens_used": result["tokens_used"]}


@router.post("/ai/class-insight/{class_id}")
async def ai_class_insight(
    class_id: int,
    template_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """AI 班级学情洞察"""
    from app.services.ai_service import ai_service

    class_obj = await db.get(Class, class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 获取班级看板数据
    dashboard = await get_class_dashboard(class_id, template_id, db, current_user)

    # 格式化数据
    dist = dashboard.distribution
    score_dist_lines = [f"- {r['range']}: {r['count']}人" for r in dist.score_ranges]
    score_distribution = "\n".join(score_dist_lines)

    dim_lines = [f"- {d['label']}: {d['avg_score']}分" for d in dashboard.weak_dims]
    dim_averages = "\n".join(dim_lines)

    top_lines = [f"{r.rank}. {r.student_name}: {r.total_score}分" for r in dashboard.ranking[:5]]
    top_students = "\n".join(top_lines)

    result = await ai_service.class_insight(
        class_name=class_obj.name,
        template_name=f"模板ID:{dashboard.template_id}",
        student_count=dist.total_students,
        avg_score=dist.average_score,
        pass_rate=dist.pass_rate,
        excellent_rate=dist.excellent_rate,
        score_distribution=score_distribution,
        dim_averages=dim_averages,
        top_students=top_students
    )

    return {"report": result["report"], "tokens_used": result["tokens_used"]}
