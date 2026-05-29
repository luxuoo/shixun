from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from openai import OpenAIError, APIError, AuthenticationError, APITimeoutError
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score
from app.schemas.submission import (
    AiHintRequest,
    AiHintResponse,
    AiAnalyzeRequest,
    AiAnalyzeResponse,
    AiScoreRequest,
    AiScoreResponse
)
from app.services.ai_service import ai_service
from app.api.auth import _system_settings

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/hint", response_model=AiHintResponse)
async def get_hint(
    request: AiHintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 检查 AI 对话是否启用
    if not _system_settings.get("ai_chat_enabled", True):
        raise HTTPException(status_code=403, detail="AI 对话功能已被管理员禁用")

    # 获取任务和步骤信息
    task_result = await db.execute(select(Task).where(Task.id == request.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    step_result = await db.execute(
        select(TaskStep).where(
            TaskStep.task_id == request.task_id,
            TaskStep.id == request.step_id
        )
    )
    step = step_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    # 获取学生当前步骤的提示次数
    hint_count_result = await db.execute(
        select(func.count(AiLog.id)).where(
            AiLog.user_id == current_user.id,
            AiLog.task_id == request.task_id,
            AiLog.step_id == request.step_id,
            AiLog.request_type == "hint"
        )
    )
    hint_count = hint_count_result.scalar() or 0

    # 确定提示次数上限：全局设置 > 步骤自带设置
    global_limit = _system_settings.get("ai_hints_limit", 0)
    hints_available = global_limit if global_limit > 0 else step.hints_available

    # 检查提示次数限制
    if hint_count >= hints_available:
        raise HTTPException(
            status_code=400,
            detail=f"本步骤最多只能请求 {hints_available} 次提示"
        )

    # 调用 AI 服务获取提示
    try:
        result = await ai_service.get_hint(
            task_title=task.title,
            step_title=step.title,
            step_requirements=step.requirements or "",
            hint_count=hint_count + 1,
            student_code=request.student_code,
            question=request.question
        )
    except AuthenticationError:
        raise HTTPException(status_code=502, detail="AI 服务认证失败，请联系管理员检查 API Key 配置")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后重试")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误：{str(e)[:200]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务不可用：{str(e)[:200]}")

    # 记录 AI 调用日志
    ai_log = AiLog(
        user_id=current_user.id,
        task_id=request.task_id,
        step_id=request.step_id,
        request_type="hint",
        hint_level=result["hint_level"],
        request_content=request.question or "请求提示",
        response_content=result["content"],
        tokens_used=result["tokens_used"]
    )
    db.add(ai_log)

    # 更新评分记录的提示次数
    score_result = await db.execute(
        select(Score).where(
            Score.user_id == current_user.id,
            Score.task_id == request.task_id
        )
    )
    score = score_result.scalar_one_or_none()
    if score:
        score.ai_hint_count = (score.ai_hint_count or 0) + 1

    await db.commit()

    return AiHintResponse(
        hint_level=result["hint_level"],
        content=result["content"],
        remaining_hints=hints_available - hint_count - 1
    )


@router.post("/analyze", response_model=AiAnalyzeResponse)
async def analyze_code(
    request: AiAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 检查 AI 对话是否启用
    if not _system_settings.get("ai_chat_enabled", True):
        raise HTTPException(status_code=403, detail="AI 对话功能已被管理员禁用")

    # 获取任务和步骤信息
    task_result = await db.execute(select(Task).where(Task.id == request.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    step_result = await db.execute(
        select(TaskStep).where(
            TaskStep.task_id == request.task_id,
            TaskStep.id == request.step_id
        )
    )
    step = step_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    # 调用 AI 服务分析代码
    try:
        result = await ai_service.analyze_code(
            code=request.code,
            step_requirements=step.requirements or "",
            task_title=task.title,
            step_title=step.title
        )
    except AuthenticationError:
        raise HTTPException(status_code=502, detail="AI 服务认证失败，请联系管理员检查 API Key 配置")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后重试")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误：{str(e)[:200]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务不可用：{str(e)[:200]}")

    # 记录 AI 调用日志
    ai_log = AiLog(
        user_id=current_user.id,
        task_id=request.task_id,
        step_id=request.step_id,
        request_type="analyze",
        request_content=request.code[:500],  # 只记录前500字符
        response_content=result["analysis"],
        tokens_used=result["tokens_used"]
    )
    db.add(ai_log)
    await db.commit()

    return AiAnalyzeResponse(
        analysis=result["analysis"],
        suggestions=[]  # 可以从分析结果中提取
    )


@router.post("/score", response_model=AiScoreResponse)
async def score_submission(
    request: AiScoreRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 获取任务和步骤信息
    task_result = await db.execute(select(Task).where(Task.id == request.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    step_result = await db.execute(
        select(TaskStep).where(
            TaskStep.task_id == request.task_id,
            TaskStep.id == request.step_id
        )
    )
    step = step_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    # 调用 AI 服务评分
    try:
        result = await ai_service.score_submission(
            code=request.code,
            step_requirements=step.requirements or "",
            task_title=task.title,
            step_title=step.title
        )
    except AuthenticationError:
        raise HTTPException(status_code=502, detail="AI 服务认证失败，请联系管理员检查 API Key 配置")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后重试")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误：{str(e)[:200]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务不可用：{str(e)[:200]}")

    # 记录 AI 调用日志
    ai_log = AiLog(
        user_id=current_user.id,
        task_id=request.task_id,
        step_id=request.step_id,
        request_type="score",
        request_content=request.code[:500],
        response_content=str(result),
        tokens_used=result["tokens_used"]
    )
    db.add(ai_log)

    # 更新最近一次提交的 AI 评分
    submission_result = await db.execute(
        select(Submission)
        .where(
            Submission.user_id == current_user.id,
            Submission.task_id == request.task_id,
            Submission.step_id == request.step_id
        )
        .order_by(Submission.submitted_at.desc())
        .limit(1)
    )
    submission = submission_result.scalar_one_or_none()
    if submission:
        submission.ai_score = result["total_score"]
        submission.ai_feedback = result["feedback"]
        submission.status = "ai_scored"

    # 更新评分记录
    score_result = await db.execute(
        select(Score).where(
            Score.user_id == current_user.id,
            Score.task_id == request.task_id
        )
    )
    score = score_result.scalar_one_or_none()
    if score:
        # 计算 AI 总评分（所有步骤的平均分）
        all_scores_result = await db.execute(
            select(func.avg(Submission.ai_score))
            .where(
                Submission.user_id == current_user.id,
                Submission.task_id == request.task_id,
                Submission.ai_score.isnot(None)
            )
        )
        avg_score = all_scores_result.scalar()
        score.ai_total_score = avg_score if avg_score else result["total_score"]

        # 计算完成率
        total_steps_result = await db.execute(
            select(func.count(TaskStep.id)).where(TaskStep.task_id == request.task_id)
        )
        total_steps = total_steps_result.scalar() or 1

        completed_steps_result = await db.execute(
            select(func.count(func.distinct(Submission.step_id)))
            .where(
                Submission.user_id == current_user.id,
                Submission.task_id == request.task_id,
                Submission.ai_score.isnot(None),
                Submission.ai_score >= 60
            )
        )
        completed_steps = completed_steps_result.scalar() or 0
        score.completion_rate = (completed_steps / total_steps) * 100

        # 计算最终分数
        if score.teacher_score:
            score.final_score = (score.ai_total_score * 0.6 + score.teacher_score * 0.4)
        else:
            score.final_score = score.ai_total_score

    await db.commit()

    return AiScoreResponse(
        total_score=result["total_score"],
        correctness=result["correctness"],
        code_style=result["code_style"],
        completion=result["completion"],
        creativity=result["creativity"],
        feedback=result["feedback"],
        suggestions=result["suggestions"]
    )


@router.get("/history")
async def get_ai_history(
    task_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(AiLog).where(AiLog.user_id == current_user.id)
    if task_id:
        query = query.where(AiLog.task_id == task_id)
    query = query.order_by(AiLog.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()
