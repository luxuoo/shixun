from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_teacher, get_current_admin
from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score, RollcallRecord
from app.schemas.submission import SubmissionReview, SubmissionResponse
from app.schemas.user import UserResponse, ClassUpdate, ClassResponse
from app.services.ai_service import ai_service
from app.core.config import settings
from app.api.auth import _system_settings

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


def calc_final_score(score) -> float:
    """统一的最终分数计算函数"""
    gw = _system_settings.get("grade_weights", {"ai": 40, "teacher": 30, "attendance": 20})
    total_weight = gw["ai"] + gw["teacher"] + gw["attendance"]
    if total_weight == 0:
        total_weight = 1

    ai = score.ai_total_score or 0
    teacher = score.teacher_score or 0
    attendance = score.attendance_score or 0
    bonus = score.bonus_score or 0

    base = (ai * gw["ai"] + teacher * gw["teacher"] + attendance * gw["attendance"]) / total_weight
    return round(base + bonus, 1)


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
            "bonus_score": round(s.bonus_score, 1) if s.bonus_score else None,
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
    return result.scalars().all()


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

    # 计算最终分数（AI 60% + 老师 40%）
    if submission.ai_score:
        submission.final_score = submission.ai_score * 0.6 + review_data.teacher_score * 0.4
    else:
        submission.final_score = review_data.teacher_score

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
    if not student_ids:
        raise HTTPException(status_code=400, detail="请选择学生")

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
            if submission.ai_score:
                submission.final_score = submission.ai_score * 0.6 + teacher_score * 0.4
            else:
                submission.final_score = teacher_score

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


# ==================== 加减分 ====================

@router.post("/students/{student_id}/adjust-score")
async def adjust_student_score(
    student_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    student_result = await db.execute(select(User).where(User.id == student_id, User.role == "student"))
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")

    task_id = data.get("task_id")
    adjustment = data.get("adjustment", 0)
    reason = data.get("reason", "")

    if adjustment == 0:
        raise HTTPException(status_code=400, detail="调整分数不能为0")

    if task_id:
        # 针对某个任务加减分
        score_result = await db.execute(
            select(Score).where(Score.user_id == student_id, Score.task_id == task_id)
        )
        score = score_result.scalar_one_or_none()
        if not score:
            # 如果没有 Score 记录，创建一个
            score = Score(user_id=student_id, task_id=task_id, total_submissions=0)
            db.add(score)
            await db.flush()

        score.bonus_score = (score.bonus_score or 0) + adjustment
        score.final_score = calc_final_score(score)
    else:
        # 全局加减分（不针对特定任务），给所有任务都加上
        scores_result = await db.execute(
            select(Score).where(Score.user_id == student_id)
        )
        scores = scores_result.scalars().all()
        for score in scores:
            score.bonus_score = (score.bonus_score or 0) + adjustment
            score.final_score = calc_final_score(score)

    await db.commit()
    return {"message": f"已{'加' if adjustment > 0 else '减'}{abs(adjustment)}分", "adjustment": adjustment}


# ==================== 成绩汇总 ====================

@router.get("/grades")
async def get_grades(
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    query = select(User).where(User.role == "student")
    if class_id:
        query = query.where(User.class_id == class_id)
    students_result = await db.execute(query.order_by(User.student_id))
    students = students_result.scalars().all()

    # 获取所有任务
    tasks_result = await db.execute(select(Task).where(Task.is_active == True).order_by(Task.id))
    tasks = tasks_result.scalars().all()

    result = []
    for student in students:
        # 获取该学生所有成绩
        scores_result = await db.execute(
            select(Score).where(Score.user_id == student.id)
        )
        scores = {s.task_id: s for s in scores_result.scalars().all()}

        task_scores = []
        total_weighted = 0
        total_bonus = 0
        total_attendance = 0
        task_count = 0

        for task in tasks:
            score = scores.get(task.id)
            if score:
                final = score.final_score or 0
                bonus = score.bonus_score or 0
                attendance = score.attendance_score or 0
                task_scores.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "ai_score": round(score.ai_total_score or 0, 1),
                    "teacher_score": round(score.teacher_score or 0, 1) if score.teacher_score else None,
                    "attendance_score": round(attendance, 1),
                    "bonus_score": round(bonus, 1),
                    "final_score": round(final, 1),
                    "rollcall_count": score.rollcall_count or 0,
                    "status": score.status
                })
                total_weighted += final
                total_bonus += bonus
                total_attendance += attendance
                task_count += 1
            else:
                task_scores.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "ai_score": None,
                    "teacher_score": None,
                    "attendance_score": 0,
                    "bonus_score": 0,
                    "final_score": None,
                    "rollcall_count": 0,
                    "status": "not_started"
                })

        avg_score = round(total_weighted / task_count, 1) if task_count > 0 else 0

        # 获取班级名
        class_name = None
        if student.class_id:
            cls_result = await db.execute(select(Class.name).where(Class.id == student.class_id))
            class_name = cls_result.scalar()

        result.append({
            "student_id": student.id,
            "student_no": student.student_id or "",
            "name": student.name or "",
            "username": student.username,
            "class_name": class_name or "",
            "task_scores": task_scores,
            "total_bonus": round(total_bonus, 1),
            "total_attendance": round(total_attendance, 1),
            "average_score": avg_score,
            "task_count": task_count
        })

    # 获取任务列表信息
    task_list = [{"id": t.id, "title": t.title} for t in tasks]

    return {"students": result, "tasks": task_list}


# ==================== 点名记录 ====================

@router.post("/rollcall")
async def record_rollcall(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """记录点名并可选自动加分"""
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

    # 更新所有 Score 记录的 rollcall_count
    scores_result = await db.execute(select(Score).where(Score.user_id == student_id))
    scores = scores_result.scalars().all()
    for score in scores:
        score.rollcall_count = (score.rollcall_count or 0) + 1

    # 如果开启自动出勤分
    rollcall_score = _system_settings.get("rollcall_score", 5)
    auto_score = _system_settings.get("rollcall_auto_score", False)
    if auto_score and rollcall_score > 0:
        for score in scores:
            score.attendance_score = (score.attendance_score or 0) + rollcall_score
            score.final_score = calc_final_score(score)

    await db.commit()
    return {"message": f"已记录 {student.name} 的出勤", "rollcall_count": (scores[0].rollcall_count if scores else 1)}


@router.get("/rollcall/today")
async def get_today_rollcall(
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取今日点名记录"""
    today = datetime.utcnow().date()
    query = select(RollcallRecord).where(func.date(RollcallRecord.created_at) == today)
    if class_id:
        query = query.where(RollcallRecord.class_id == class_id)
    result = await db.execute(query)
    records = result.scalars().all()
    return {"student_ids": [r.student_id for r in records], "count": len(records)}


@router.post("/attendance")
async def set_attendance_score(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """手动设置学生出勤分"""
    student_id = data.get("student_id")
    task_id = data.get("task_id")
    score_value = data.get("score", 0)

    if not student_id:
        raise HTTPException(status_code=400, detail="请选择学生")

    if task_id:
        # 针对特定任务
        score_result = await db.execute(
            select(Score).where(Score.user_id == student_id, Score.task_id == task_id)
        )
        score = score_result.scalar_one_or_none()
        if not score:
            score = Score(user_id=student_id, task_id=task_id, total_submissions=0)
            db.add(score)
            await db.flush()
        score.attendance_score = score_value
        score.final_score = calc_final_score(score)
    else:
        # 所有任务
        scores_result = await db.execute(select(Score).where(Score.user_id == student_id))
        scores = scores_result.scalars().all()
        for score in scores:
            score.attendance_score = score_value
            score.final_score = calc_final_score(score)

    await db.commit()
    return {"message": f"出勤分已设置为 {score_value}"}


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
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
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


# ==================== 成绩方案管理 ====================

from app.models.grade import GradeScheme, GradeItem, GradeRecord


@router.get("/grade-schemes")
async def get_grade_schemes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取所有成绩方案"""
    result = await db.execute(select(GradeScheme).order_by(GradeScheme.created_at.desc()))
    schemes = result.scalars().all()
    response = []
    for s in schemes:
        # 获取班级名
        class_name = None
        if s.class_id:
            cls_result = await db.execute(select(Class.name).where(Class.id == s.class_id))
            class_name = cls_result.scalar()
        # 获取计分项目
        items_result = await db.execute(
            select(GradeItem).where(GradeItem.scheme_id == s.id).order_by(GradeItem.sort_order)
        )
        items = items_result.scalars().all()
        weight_total = sum(i.weight for i in items)
        response.append({
            "id": s.id, "name": s.name, "class_id": s.class_id,
            "class_name": class_name, "decimal_places": s.decimal_places,
            "is_active": s.is_active, "created_by": s.created_by,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "items": [{"id": i.id, "scheme_id": i.scheme_id, "name": i.name,
                       "weight": i.weight, "max_score": i.max_score,
                       "sort_order": i.sort_order} for i in items],
            "weight_total": weight_total
        })
    return response


@router.post("/grade-schemes")
async def create_grade_scheme(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """创建成绩方案"""
    scheme = GradeScheme(
        name=data.get("name", "新方案"),
        class_id=data.get("class_id"),
        decimal_places=data.get("decimal_places", 1),
        created_by=current_user.id
    )
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    return {"id": scheme.id, "message": "方案创建成功"}


@router.put("/grade-schemes/{scheme_id}")
async def update_grade_scheme(
    scheme_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """更新成绩方案"""
    result = await db.execute(select(GradeScheme).where(GradeScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="方案不存在")
    if "name" in data:
        scheme.name = data["name"]
    if "class_id" in data:
        scheme.class_id = data["class_id"]
    if "decimal_places" in data:
        scheme.decimal_places = max(0, min(3, int(data["decimal_places"])))
    await db.commit()
    return {"message": "方案更新成功"}


@router.delete("/grade-schemes/{scheme_id}")
async def delete_grade_scheme(
    scheme_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除成绩方案"""
    result = await db.execute(select(GradeScheme).where(GradeScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="方案不存在")
    await db.delete(scheme)
    await db.commit()
    return {"message": "方案已删除"}


@router.post("/grade-schemes/{scheme_id}/activate")
async def activate_grade_scheme(
    scheme_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """激活成绩方案"""
    # 先取消所有方案的激活状态
    await db.execute(update(GradeScheme).values(is_active=False))
    # 激活指定方案
    result = await db.execute(select(GradeScheme).where(GradeScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="方案不存在")
    scheme.is_active = True
    await db.commit()
    return {"message": f"方案 '{scheme.name}' 已激活"}


# ==================== 计分项目管理 ====================

@router.get("/grade-schemes/{scheme_id}/items")
async def get_grade_items(
    scheme_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取方案下的计分项目"""
    result = await db.execute(
        select(GradeItem).where(GradeItem.scheme_id == scheme_id).order_by(GradeItem.sort_order)
    )
    return result.scalars().all()


@router.post("/grade-schemes/{scheme_id}/items")
async def create_grade_item(
    scheme_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """添加计分项目"""
    # 验证方案存在
    scheme_result = await db.execute(select(GradeScheme).where(GradeScheme.id == scheme_id))
    if not scheme_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="方案不存在")
    # 验证权重总和
    items_result = await db.execute(select(GradeItem).where(GradeItem.scheme_id == scheme_id))
    existing_items = items_result.scalars().all()
    current_total = sum(i.weight for i in existing_items)
    new_weight = data.get("weight", 0)
    if current_total + new_weight > 100:
        raise HTTPException(status_code=400, detail=f"权重总和将超过100%（当前{current_total}%+{new_weight}%）")
    item = GradeItem(
        scheme_id=scheme_id,
        name=data.get("name", ""),
        weight=new_weight,
        max_score=data.get("max_score", 100),
        sort_order=data.get("sort_order", len(existing_items))
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "message": "计分项目添加成功"}


@router.put("/grade-items/{item_id}")
async def update_grade_item(
    item_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """更新计分项目"""
    result = await db.execute(select(GradeItem).where(GradeItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="计分项目不存在")
    if "name" in data:
        item.name = data["name"]
    if "weight" in data:
        # 验证权重总和
        siblings_result = await db.execute(
            select(GradeItem).where(GradeItem.scheme_id == item.scheme_id, GradeItem.id != item_id)
        )
        siblings = siblings_result.scalars().all()
        other_total = sum(i.weight for i in siblings)
        new_weight = data["weight"]
        if other_total + new_weight > 100:
            raise HTTPException(status_code=400, detail=f"权重总和将超过100%（其他项目{other_total}%+{new_weight}%）")
        item.weight = new_weight
    if "max_score" in data:
        item.max_score = data["max_score"]
    if "sort_order" in data:
        item.sort_order = data["sort_order"]
    await db.commit()
    return {"message": "计分项目更新成功"}


@router.delete("/grade-items/{item_id}")
async def delete_grade_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """删除计分项目"""
    result = await db.execute(select(GradeItem).where(GradeItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="计分项目不存在")
    await db.delete(item)
    await db.commit()
    return {"message": "计分项目已删除"}


# ==================== 成绩录入与查询 ====================

def _calc_student_total(records: list, items: list, decimal_places: int = 1) -> float:
    """计算学生总成绩"""
    item_map = {i.id: i for i in items}
    total_weight = 0
    weighted_sum = 0
    for r in records:
        item = item_map.get(r.item_id)
        if item and r.score is not None and r.status != "absent":
            weighted_sum += (r.score / item.max_score) * item.weight
            total_weight += item.weight
    if total_weight == 0:
        return 0
    return round(weighted_sum / total_weight * 100, decimal_places)


@router.get("/grades/records")
async def get_grade_records(
    scheme_id: int = None,
    class_id: int = None,
    student_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """获取成绩列表"""
    # 获取激活的方案
    if not scheme_id:
        active_result = await db.execute(select(GradeScheme).where(GradeScheme.is_active == True))
        active_scheme = active_result.scalar_one_or_none()
        if not active_scheme:
            return {"scheme": None, "students": [], "items": []}
        scheme_id = active_scheme.id

    # 获取方案和计分项目
    scheme_result = await db.execute(select(GradeScheme).where(GradeScheme.id == scheme_id))
    scheme = scheme_result.scalar_one_or_none()
    if not scheme:
        raise HTTPException(status_code=404, detail="方案不存在")

    items_result = await db.execute(
        select(GradeItem).where(GradeItem.scheme_id == scheme_id).order_by(GradeItem.sort_order)
    )
    items = items_result.scalars().all()

    # 获取学生列表
    student_query = select(User).where(User.role == "student")
    if class_id:
        student_query = student_query.where(User.class_id == class_id)
    if student_id:
        student_query = student_query.where(User.id == student_id)
    students_result = await db.execute(student_query.order_by(User.student_id))
    students = students_result.scalars().all()

    # 获取所有成绩记录
    student_ids = [s.id for s in students]
    item_ids = [i.id for i in items]
    if not student_ids or not item_ids:
        return {
            "scheme": {"id": scheme.id, "name": scheme.name, "decimal_places": scheme.decimal_places},
            "items": [{"id": i.id, "name": i.name, "weight": i.weight, "max_score": i.max_score} for i in items],
            "students": []
        }

    records_result = await db.execute(
        select(GradeRecord).where(
            GradeRecord.student_id.in_(student_ids),
            GradeRecord.item_id.in_(item_ids)
        )
    )
    all_records = records_result.scalars().all()
    records_map = {}
    for r in all_records:
        records_map[(r.student_id, r.item_id)] = r

    # 构建响应
    result = []
    for student in students:
        class_name = None
        if student.class_id:
            cls_r = await db.execute(select(Class.name).where(Class.id == student.class_id))
            class_name = cls_r.scalar()
        student_records = [records_map.get((student.id, i.id)) for i in items]
        total = _calc_student_total(
            [r for r in student_records if r], items, scheme.decimal_places
        )
        item_scores = []
        for i, r in zip(items, student_records):
            item_scores.append({
                "item_id": i.id, "item_name": i.name, "weight": i.weight,
                "max_score": i.max_score,
                "score": r.score if r else None,
                "remark": r.remark if r else None,
                "status": r.status if r else "normal",
                "record_id": r.id if r else None
            })
        result.append({
            "student_id": student.id,
            "student_no": student.student_id or "",
            "student_name": student.name or "",
            "class_name": class_name or "",
            "items": item_scores,
            "total_score": total
        })

    return {
        "scheme": {"id": scheme.id, "name": scheme.name, "decimal_places": scheme.decimal_places},
        "items": [{"id": i.id, "name": i.name, "weight": i.weight, "max_score": i.max_score} for i in items],
        "students": result
    }


@router.post("/grades/records")
async def save_grade_record(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """录入/更新单条成绩"""
    student_id = data.get("student_id")
    item_id = data.get("item_id")
    score = data.get("score")
    remark = data.get("remark", "")
    status = data.get("status", "normal")

    if not student_id or not item_id:
        raise HTTPException(status_code=400, detail="缺少学生或计分项目")

    # 验证分数合法性
    item_result = await db.execute(select(GradeItem).where(GradeItem.id == item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="计分项目不存在")
    if score is not None and (score < 0 or score > item.max_score):
        raise HTTPException(status_code=400, detail=f"分数必须在0-{item.max_score}之间")

    # 查找或创建记录
    record_result = await db.execute(
        select(GradeRecord).where(GradeRecord.student_id == student_id, GradeRecord.item_id == item_id)
    )
    record = record_result.scalar_one_or_none()
    if record:
        record.score = score
        record.remark = remark
        record.status = status
        record.recorded_by = current_user.id
    else:
        record = GradeRecord(
            student_id=student_id, item_id=item_id, score=score,
            remark=remark, status=status, recorded_by=current_user.id
        )
        db.add(record)
    await db.commit()
    return {"message": "成绩已保存"}


@router.post("/grades/records/batch")
async def batch_import_grades(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """批量导入成绩"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="没有成绩数据")
    success = 0
    errors = []
    for r in records:
        try:
            student_id = r.get("student_id")
            item_id = r.get("item_id")
            score = r.get("score")
            if not student_id or not item_id:
                continue
            # 验证分数
            item_result = await db.execute(select(GradeItem).where(GradeItem.id == item_id))
            item = item_result.scalar_one_or_none()
            if not item:
                continue
            if score is not None and (score < 0 or score > item.max_score):
                errors.append(f"学生{student_id}的{item.name}分数超出范围")
                continue
            # 查找或创建
            record_result = await db.execute(
                select(GradeRecord).where(GradeRecord.student_id == student_id, GradeRecord.item_id == item_id)
            )
            record = record_result.scalar_one_or_none()
            if record:
                record.score = score
                record.recorded_by = current_user.id
            else:
                record = GradeRecord(
                    student_id=student_id, item_id=item_id, score=score,
                    recorded_by=current_user.id
                )
                db.add(record)
            success += 1
        except Exception as e:
            errors.append(str(e))
    await db.commit()
    return {"success": success, "errors": errors}


@router.delete("/grades/records/{record_id}")
async def delete_grade_record(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """撤销成绩记录"""
    result = await db.execute(select(GradeRecord).where(GradeRecord.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.delete(record)
    await db.commit()
    return {"message": "成绩记录已撤销"}


@router.get("/grades/statistics")
async def get_grade_statistics(
    scheme_id: int = None,
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """班级成绩统计"""
    if not scheme_id:
        active_result = await db.execute(select(GradeScheme).where(GradeScheme.is_active == True))
        active_scheme = active_result.scalar_one_or_none()
        if not active_scheme:
            return {"statistics": [], "total_stats": {}}
        scheme_id = active_scheme.id

    items_result = await db.execute(
        select(GradeItem).where(GradeItem.scheme_id == scheme_id).order_by(GradeItem.sort_order)
    )
    items = items_result.scalars().all()

    # 获取学生
    student_query = select(User).where(User.role == "student")
    if class_id:
        student_query = student_query.where(User.class_id == class_id)
    students_result = await db.execute(student_query)
    students = students_result.scalars().all()
    student_ids = [s.id for s in students]

    if not student_ids or not items:
        return {"statistics": [], "total_stats": {}}

    stats = []
    for item in items:
        records_result = await db.execute(
            select(GradeRecord).where(
                GradeRecord.item_id == item.id,
                GradeRecord.student_id.in_(student_ids),
                GradeRecord.score.isnot(None)
            )
        )
        records = records_result.scalars().all()
        scores = [r.score for r in records if r.status != "absent"]
        if scores:
            passed = sum(1 for s in scores if s / item.max_score >= 0.6)
            stats.append({
                "item_name": item.name,
                "count": len(scores),
                "avg": round(sum(scores) / len(scores), 1),
                "max": max(scores),
                "min": min(scores),
                "pass_rate": round(passed / len(scores) * 100, 1)
            })

    # 总成绩统计
    total_scores = []
    for student in students:
        records_result = await db.execute(
            select(GradeRecord).where(GradeRecord.student_id == student.id, GradeRecord.item_id.in_([i.id for i in items]))
        )
        records = records_result.scalars().all()
        total = _calc_student_total(records, items, 1)
        if total > 0:
            total_scores.append(total)

    total_stats = {}
    if total_scores:
        total_stats = {
            "count": len(total_scores),
            "avg": round(sum(total_scores) / len(total_scores), 1),
            "max": max(total_scores),
            "min": min(total_scores),
            "pass_rate": round(sum(1 for s in total_scores if s >= 60) / len(total_scores) * 100, 1)
        }

    return {"statistics": stats, "total_stats": total_stats}


@router.get("/grades/export")
async def export_grades(
    scheme_id: int = None,
    class_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """导出成绩数据"""
    # 复用 get_grade_records 的逻辑
    data = await get_grade_records(scheme_id=scheme_id, class_id=class_id, student_id=None, db=db, current_user=current_user)
    return data


# ==================== 学生端成绩查询 ====================

@router.get("/student/grades")
async def get_student_grades(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """学生查看自己的成绩"""
    # 检查开关
    if not _system_settings.get("student_view_grades", True):
        raise HTTPException(status_code=403, detail="成绩查看功能暂未开放")

    # 获取激活的方案
    active_result = await db.execute(select(GradeScheme).where(GradeScheme.is_active == True))
    scheme = active_result.scalar_one_or_none()
    if not scheme:
        return {"scheme": None, "items": [], "total_score": None}

    # 获取计分项目
    items_result = await db.execute(
        select(GradeItem).where(GradeItem.scheme_id == scheme.id).order_by(GradeItem.sort_order)
    )
    items = items_result.scalars().all()

    # 获取成绩记录
    records_result = await db.execute(
        select(GradeRecord).where(
            GradeRecord.student_id == current_user.id,
            GradeRecord.item_id.in_([i.id for i in items])
        )
    )
    records = records_result.scalars().all()
    records_map = {r.item_id: r for r in records}

    total = _calc_student_total(records, items, scheme.decimal_places)

    item_scores = []
    for item in items:
        r = records_map.get(item.id)
        item_scores.append({
            "item_id": item.id, "item_name": item.name,
            "weight": item.weight, "max_score": item.max_score,
            "score": r.score if r else None,
            "remark": r.remark if r else None,
            "status": r.status if r else "normal"
        })

    return {
        "scheme": {"id": scheme.id, "name": scheme.name, "decimal_places": scheme.decimal_places},
        "items": item_scores,
        "total_score": total
    }
