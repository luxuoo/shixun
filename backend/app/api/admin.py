from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime, timedelta, timezone
from app.core.database import get_db
from app.core.security import get_current_teacher, get_current_admin, get_current_user
from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score, RollcallRecord
from app.schemas.submission import SubmissionReview, SubmissionResponse
from app.schemas.user import UserResponse, ClassUpdate, ClassResponse
from app.services.ai_service import ai_service
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


def calc_final_score(score) -> float:
    """统一的最终分数计算函数，使用 grade_weights 配置

    grade_weights 示例: {"ai": 40, "teacher": 30, "attendance": 20}
    剩余权重归入 bonus_score。各项按满分100标准化后加权。
    """
    from app.api.auth import _system_settings

    weights = _system_settings.get("grade_weights", {"ai": 60, "teacher": 40, "attendance": 0})
    w_ai = weights.get("ai", 60)
    w_teacher = weights.get("teacher", 40)
    w_attendance = weights.get("attendance", 0)

    ai = score.ai_total_score or 0
    teacher = score.teacher_score or 0
    attendance = score.attendance_score or 0
    bonus = score.bonus_score or 0

    # 如果教师未评分，教师权重归入 AI
    if score.teacher_score is None:
        w_ai_total = w_ai + w_teacher
        weighted = ai * (w_ai_total / 100) + attendance * (w_attendance / 100) + bonus
    else:
        weighted = ai * (w_ai / 100) + teacher * (w_teacher / 100) + attendance * (w_attendance / 100) + bonus

    return round(min(100, weighted), 1)


@router.get("/ai-test")
async def test_ai_connection(
    current_user: User = Depends(get_current_admin)
):
    """测试 AI 服务连接（仅管理员）"""
    import openai
    result = {
        "api_url": settings.MIMO_API_URL,
        "model": settings.MIMO_MODEL,
        "api_key_set": bool(settings.MIMO_API_KEY),
        "api_key_prefix": settings.MIMO_API_KEY[:10] + "..." if settings.MIMO_API_KEY else "未设置",
        "openai_version": openai.__version__,
        "test_result": None,
        "error": None
    }

    try:
        resp = await ai_service.client.chat.completions.create(
            model=settings.MIMO_MODEL,
            messages=[{"role": "user", "content": "请用中文回复：你好"}],
            max_tokens=200
        )
        msg = resp.choices[0].message
        content = msg.content or ""

        # 尝试多种方式获取 reasoning_content
        reasoning = getattr(msg, "reasoning_content", None)
        if not reasoning and hasattr(msg, "model_extra"):
            extra = msg.model_extra or {}
            reasoning = extra.get("reasoning_content")
        if not reasoning and hasattr(msg, "to_dict"):
            d = msg.to_dict()
            reasoning = d.get("reasoning_content")
        reasoning = reasoning or ""

        result["test_result"] = {
            "content": content[:300],
            "reasoning": reasoning[:300],
            "content_empty": not content.strip(),
            "reasoning_empty": not reasoning.strip(),
            "tokens": resp.usage.total_tokens if resp.usage else 0
        }
        if content.strip():
            result["status"] = "ok"
        elif reasoning.strip():
            result["status"] = "reasoning_only"
        else:
            result["status"] = "content_empty"
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"{type(e).__name__}: {str(e)[:300]}"

    return result


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # 学生总数
    students_count = await db.execute(
        select(func.count(User.id)).where(User.role == "student")
    )
    total_students = students_count.scalar() or 0

    # 任务总数
    tasks_count = await db.execute(select(func.count(Task.id)))
    total_tasks = tasks_count.scalar() or 0

    # 提交总数
    submissions_count = await db.execute(select(func.count(Submission.id)))
    total_submissions = submissions_count.scalar() or 0

    # AI 调用总数
    ai_calls_count = await db.execute(select(func.count(AiLog.id)))
    total_ai_calls = ai_calls_count.scalar() or 0

    # 平均分
    avg_score_result = await db.execute(
        select(func.avg(Score.final_score)).where(Score.final_score.isnot(None))
    )
    avg_score = avg_score_result.scalar() or 0

    # 完成率统计
    completed_count = await db.execute(
        select(func.count(Score.id)).where(Score.status == "completed")
    )
    completed_tasks = completed_count.scalar() or 0

    return {
        "total_students": total_students,
        "total_tasks": total_tasks,
        "total_submissions": total_submissions,
        "total_ai_calls": total_ai_calls,
        "average_score": round(avg_score, 1),
        "completed_tasks": completed_tasks
    }


@router.get("/students", response_model=list[UserResponse])
async def get_students(
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    query = select(User).where(User.role == "student")
    if class_id:
        query = query.where(User.class_id == class_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.delete("/students/{student_id}")
async def delete_student(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """删除学生及其所有关联数据"""
    student = await db.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if student.role != "student":
        raise HTTPException(status_code=400, detail="只能删除学生账号")

    # 按顺序删除关联数据（外键无 CASCADE，需手动清理）
    await db.execute(delete(RollcallRecord).where(RollcallRecord.student_id == student_id))
    await db.execute(delete(Score).where(Score.user_id == student_id))
    await db.execute(delete(AiLog).where(AiLog.user_id == student_id))
    await db.execute(delete(Submission).where(Submission.user_id == student_id))

    await db.delete(student)
    await db.commit()
    return {"message": "学生已删除"}


@router.get("/students/{student_id}")
async def get_student_detail(
    student_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # 获取学生信息
    student_result = await db.execute(select(User).where(User.id == student_id))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 获取学生的任务完成情况（手动序列化，避免 SQLAlchemy 对象序列化问题）
    scores_result = await db.execute(
        select(Score).where(Score.user_id == student_id)
    )
    scores = scores_result.scalars().all()

    # 获取任务标题映射
    tasks_result = await db.execute(select(Task.id, Task.title))
    task_map = {row[0]: row[1] for row in tasks_result}

    score_list = []
    for s in scores:
        score_list.append({
            "id": s.id,
            "user_id": s.user_id,
            "task_id": s.task_id,
            "task_title": task_map.get(s.task_id, f"任务 #{s.task_id}"),
            "ai_total_score": round(s.ai_total_score, 1) if s.ai_total_score else None,
            "completion_rate": round(s.completion_rate, 1) if s.completion_rate else None,
            "teacher_score": round(s.teacher_score, 1) if s.teacher_score else None,
            "final_score": round(s.final_score, 1) if s.final_score else None,
            "ai_hint_count": s.ai_hint_count,
            "total_submissions": s.total_submissions,
            "status": s.status
        })

    # 获取学生的提交统计
    submissions_count = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == student_id)
    )
    total_submissions = submissions_count.scalar() or 0

    # 获取 AI 使用统计
    ai_usage = await db.execute(
        select(func.count(AiLog.id)).where(AiLog.user_id == student_id)
    )
    total_ai_calls = ai_usage.scalar() or 0

    return {
        "student": UserResponse.model_validate(student),
        "scores": score_list,
        "total_submissions": total_submissions,
        "total_ai_calls": total_ai_calls
    }


@router.get("/submissions", response_model=list[SubmissionResponse])
async def get_all_submissions(
    task_id: int = None,
    user_id: int = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    query = select(Submission)
    if task_id:
        query = query.where(Submission.task_id == task_id)
    if user_id:
        query = query.where(Submission.user_id == user_id)
    if status:
        query = query.where(Submission.status == status)
    query = query.order_by(Submission.submitted_at.desc())
    result = await db.execute(query)
    submissions = result.scalars().all()

    # 补充关联信息（用户名、任务标题）
    enriched = []
    for sub in submissions:
        resp = SubmissionResponse.model_validate(sub)
        # 获取用户名
        user_result = await db.execute(select(User.name, User.username).where(User.id == sub.user_id))
        user_row = user_result.first()
        if user_row:
            resp.user_name = user_row[0]
            resp.username = user_row[1]
        # 获取任务标题
        task_result = await db.execute(select(Task.title).where(Task.id == sub.task_id))
        resp.task_title = task_result.scalar()
        enriched.append(resp)

    return enriched


@router.put("/submissions/{submission_id}/score")
async def review_submission(
    submission_id: int,
    review_data: SubmissionReview,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # 获取提交记录
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    # 更新老师评分
    submission.teacher_score = review_data.teacher_score
    submission.teacher_comment = review_data.teacher_comment
    submission.status = "reviewed"
    submission.reviewed_at = datetime.now(timezone.utc)

    # 计算提交级最终分数（AI 60% + 老师 40%）
    if submission.ai_score:
        submission.final_score = round(submission.ai_score * 0.6 + review_data.teacher_score * 0.4, 1)
    else:
        submission.final_score = round(review_data.teacher_score, 1)

    # 更新评分记录
    score_result = await db.execute(
        select(Score).where(
            Score.user_id == submission.user_id,
            Score.task_id == submission.task_id
        )
    )
    score = score_result.scalar_one_or_none()
    if score:
        score.teacher_score = review_data.teacher_score
        score.final_score = calc_final_score(score)
        score.status = "reviewed"

    await db.commit()

    return {"message": "评分成功", "final_score": submission.final_score}


@router.get("/ai-stats")
async def get_ai_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # AI 调用类型统计
    type_stats = await db.execute(
        select(
            AiLog.request_type,
            func.count(AiLog.id).label("count")
        )
        .group_by(AiLog.request_type)
    )
    type_distribution = {row[0]: row[1] for row in type_stats}

    # 提示级别统计
    level_stats = await db.execute(
        select(
            AiLog.hint_level,
            func.count(AiLog.id).label("count")
        )
        .where(AiLog.request_type == "hint")
        .group_by(AiLog.hint_level)
    )
    level_distribution = {f"level_{row[0]}": row[1] for row in level_stats}

    # Token 使用统计
    token_stats = await db.execute(
        select(func.sum(AiLog.tokens_used))
    )
    total_tokens = token_stats.scalar() or 0

    # 每日调用统计（最近7天）
    daily_stats = await db.execute(
        select(
            func.date(AiLog.created_at).label("date"),
            func.count(AiLog.id).label("count")
        )
        .group_by(func.date(AiLog.created_at))
        .order_by(func.date(AiLog.created_at).desc())
        .limit(7)
    )
    daily_calls = [{"date": str(row[0]), "count": row[1]} for row in daily_stats]

    return {
        "type_distribution": type_distribution,
        "level_distribution": level_distribution,
        "total_tokens": total_tokens,
        "daily_calls": daily_calls
    }


# ==================== 班级管理 ====================

@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(select(Class))
    classes = result.scalars().all()
    # 补充教师姓名和学生人数
    response = []
    for c in classes:
        teacher_name = None
        if c.teacher_id:
            teacher_result = await db.execute(select(User.name).where(User.id == c.teacher_id))
            teacher_name = teacher_result.scalar()
        count_result = await db.execute(
            select(func.count(User.id)).where(User.class_id == c.id, User.role == "student")
        )
        student_count = count_result.scalar() or 0
        response.append(ClassResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            teacher_id=c.teacher_id,
            created_at=c.created_at,
            teacher_name=teacher_name,
            student_count=student_count
        ))
    return response


@router.put("/classes/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: int,
    class_data: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    update_data = class_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cls, key, value)

    await db.commit()
    await db.refresh(cls)
    return cls


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 将该班级的学生的 class_id 置空
    await db.execute(
        update(User).where(User.class_id == class_id).values(class_id=None)
    )
    await db.delete(cls)
    await db.commit()
    return {"message": "班级已删除"}


@router.post("/classes/{class_id}/students")
async def assign_students_to_class(
    class_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(select(Class).where(Class.id == class_id))
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    student_ids = data.get("student_ids", [])

    # 先把该班级中原有的学生全部移除（class_id 置空）
    await db.execute(
        update(User)
        .where(User.class_id == class_id, User.role == "student")
        .values(class_id=None)
    )

    # 再把选中的学生分配到该班级
    if student_ids:
        await db.execute(
            update(User)
            .where(User.id.in_(student_ids), User.role == "student")
            .values(class_id=class_id)
        )

    await db.commit()
    return {"message": f"已分配 {len(student_ids)} 名学生到班级"}


# ==================== 批量评分 ====================

@router.post("/submissions/batch-score")
async def batch_score_submissions(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    submission_ids = data.get("submission_ids", [])
    teacher_score = data.get("teacher_score")
    teacher_comment = data.get("teacher_comment", "")

    if not submission_ids:
        raise HTTPException(status_code=400, detail="请选择提交记录")
    if teacher_score is None:
        raise HTTPException(status_code=400, detail="请输入评分")

    success_count = 0
    for sid in submission_ids:
        result = await db.execute(select(Submission).where(Submission.id == sid))
        submission = result.scalar_one_or_none()
        if submission:
            submission.teacher_score = teacher_score
            submission.teacher_comment = teacher_comment
            submission.status = "reviewed"
            submission.reviewed_at = datetime.now(timezone.utc)
            if submission.ai_score:
                submission.final_score = round(submission.ai_score * 0.6 + teacher_score * 0.4, 1)
            else:
                submission.final_score = round(teacher_score, 1)

            # 更新评分记录
            score_result = await db.execute(
                select(Score).where(
                    Score.user_id == submission.user_id,
                    Score.task_id == submission.task_id
                )
            )
            score = score_result.scalar_one_or_none()
            if score:
                score.teacher_score = teacher_score
                score.final_score = calc_final_score(score)
                score.status = "reviewed"

            success_count += 1

    await db.commit()
    return {"message": f"成功评分 {success_count} 条提交记录"}


# ==================== 班级情况统计 ====================

@router.get("/classes/{class_id}/stats")
async def get_class_stats(
    class_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # 班级信息
    class_result = await db.execute(select(Class).where(Class.id == class_id))
    cls = class_result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 班级学生
    students_result = await db.execute(
        select(User).where(User.class_id == class_id, User.role == "student")
    )
    students = students_result.scalars().all()
    student_ids = [s.id for s in students]

    if not student_ids:
        return {
            "class_name": cls.name,
            "total_students": 0,
            "score_distribution": {},
            "rankings": [],
            "task_completion": {},
            "average_score": 0
        }

    # 成绩分布
    scores_result = await db.execute(
        select(Score).where(Score.user_id.in_(student_ids), Score.final_score.isnot(None))
    )
    scores = scores_result.scalars().all()

    distribution = {"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "0-59": 0}
    total_score = 0
    for s in scores:
        fs = s.final_score or 0
        total_score += fs
        if fs >= 90:
            distribution["90-100"] += 1
        elif fs >= 80:
            distribution["80-89"] += 1
        elif fs >= 70:
            distribution["70-79"] += 1
        elif fs >= 60:
            distribution["60-69"] += 1
        else:
            distribution["0-59"] += 1

    avg_score = total_score / len(scores) if scores else 0

    # 学生排名
    student_scores = {}
    for s in scores:
        if s.user_id not in student_scores:
            student_scores[s.user_id] = {"total": 0, "count": 0}
        student_scores[s.user_id]["total"] += s.final_score or 0
        student_scores[s.user_id]["count"] += 1

    rankings = []
    for student in students:
        ss = student_scores.get(student.id, {"total": 0, "count": 0})
        avg = ss["total"] / ss["count"] if ss["count"] > 0 else 0
        rankings.append({
            "student_id": student.id,
            "name": student.name,
            "username": student.username,
            "average_score": round(avg, 1),
            "task_count": ss["count"]
        })
    rankings.sort(key=lambda x: x["average_score"], reverse=True)

    # 任务完成情况
    tasks_result = await db.execute(select(Task).where(Task.is_active == True))
    tasks = tasks_result.scalars().all()

    task_completion = {}
    for task in tasks:
        task_scores_result = await db.execute(
            select(Score).where(
                Score.user_id.in_(student_ids),
                Score.task_id == task.id
            )
        )
        task_scores = task_scores_result.scalars().all()
        completed = sum(1 for s in task_scores if s.status in ("completed", "reviewed"))
        task_completion[task.title] = {
            "total_students": len(students),
            "completed": completed,
            "completion_rate": round(completed / len(students) * 100, 1) if students else 0
        }

    return {
        "class_name": cls.name,
        "total_students": len(students),
        "score_distribution": distribution,
        "rankings": rankings[:20],
        "task_completion": task_completion,
        "average_score": round(avg_score, 1)
    }


# ==================== AI 日志明细 ====================

@router.get("/ai-logs")
async def get_ai_logs(
    user_id: int = None,
    request_type: str = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    query = select(AiLog)
    count_query = select(func.count(AiLog.id))

    if user_id:
        query = query.where(AiLog.user_id == user_id)
        count_query = count_query.where(AiLog.user_id == user_id)
    if request_type:
        query = query.where(AiLog.request_type == request_type)
        count_query = count_query.where(AiLog.request_type == request_type)

    # 总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页
    query = query.order_by(AiLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    # 补充用户名和任务名
    items = []
    for log in logs:
        user_result = await db.execute(select(User.name, User.username).where(User.id == log.user_id))
        user_row = user_result.first()
        task_title = None
        if log.task_id:
            task_result = await db.execute(select(Task.title).where(Task.id == log.task_id))
            task_title = task_result.scalar()
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": user_row[0] if user_row else None,
            "username": user_row[1] if user_row else None,
            "task_id": log.task_id,
            "task_title": task_title,
            "step_id": log.step_id,
            "request_type": log.request_type,
            "hint_level": log.hint_level,
            "request_content": log.request_content,
            "response_content": log.response_content,
            "tokens_used": log.tokens_used,
            "created_at": log.created_at.isoformat() if log.created_at else None
        })

    return {"total": total, "items": items, "page": page, "page_size": page_size}


# ==================== 点名记录 ====================

@router.post("/rollcall")
async def record_rollcall(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """记录点名并可选自动加分"""
    from app.api.auth import _system_settings

    student_id = data.get("student_id")
    class_id = data.get("class_id")

    if not student_id:
        raise HTTPException(status_code=400, detail="请选择学生")

    # 验证学生存在
    student_result = await db.execute(select(User).where(User.id == student_id, User.role == "student"))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    # 记录点名
    record = RollcallRecord(student_id=student_id, class_id=class_id)
    db.add(record)

    # 如果开启了自动出勤加分，更新该学生所有任务的 Score 记录
    if _system_settings.get("rollcall_auto_score", False):
        rollcall_score = _system_settings.get("rollcall_score", 5)
        scores_result = await db.execute(
            select(Score).where(Score.user_id == student_id)
        )
        scores = scores_result.scalars().all()
        for score in scores:
            score.attendance_score = (score.attendance_score or 0) + rollcall_score
            score.rollcall_count = (score.rollcall_count or 0) + 1
            # 重新计算最终分数
            score.final_score = calc_final_score(score)

    await db.commit()
    return {"message": f"已记录 {student.name} 的出勤"}


@router.get("/rollcall/today")
async def get_today_rollcall(
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取今日点名记录"""
    today = datetime.now(timezone.utc).date()
    query = select(RollcallRecord).where(func.date(RollcallRecord.created_at) == today)
    if class_id:
        query = query.where(RollcallRecord.class_id == class_id)
    result = await db.execute(query)
    records = result.scalars().all()
    return {"student_ids": [r.student_id for r in records], "count": len(records)}


# ==================== 系统统计 ====================

@router.get("/system-stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    # 用户统计
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0

    role_stats_result = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    role_distribution = {row[0]: row[1] for row in role_stats_result}

    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_users_result.scalar() or 0

    # 最近7天注册趋势
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    reg_trend_result = await db.execute(
        select(
            func.date(User.created_at).label("date"),
            func.count(User.id).label("count")
        )
        .where(User.created_at >= seven_days_ago)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
    )
    registration_trend = [{"date": str(row[0]), "count": row[1]} for row in reg_trend_result]

    # 提交统计
    total_submissions_result = await db.execute(select(func.count(Submission.id)))
    total_submissions = total_submissions_result.scalar() or 0

    # 最近7天提交趋势
    submit_trend_result = await db.execute(
        select(
            func.date(Submission.submitted_at).label("date"),
            func.count(Submission.id).label("count")
        )
        .where(Submission.submitted_at >= seven_days_ago)
        .group_by(func.date(Submission.submitted_at))
        .order_by(func.date(Submission.submitted_at))
    )
    submission_trend = [{"date": str(row[0]), "count": row[1]} for row in submit_trend_result]

    # AI 调用统计
    total_ai_calls_result = await db.execute(select(func.count(AiLog.id)))
    total_ai_calls = total_ai_calls_result.scalar() or 0

    total_tokens_result = await db.execute(select(func.coalesce(func.sum(AiLog.tokens_used), 0)))
    total_tokens = total_tokens_result.scalar() or 0

    # 班级和任务统计
    total_classes_result = await db.execute(select(func.count(Class.id)))
    total_classes = total_classes_result.scalar() or 0

    total_tasks_result = await db.execute(select(func.count(Task.id)))
    total_tasks = total_tasks_result.scalar() or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "role_distribution": role_distribution,
        "registration_trend": registration_trend,
        "total_submissions": total_submissions,
        "submission_trend": submission_trend,
        "total_ai_calls": total_ai_calls,
        "total_tokens": total_tokens,
        "total_classes": total_classes,
        "total_tasks": total_tasks
    }
