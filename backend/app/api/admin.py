from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_teacher, get_current_admin
from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score
from app.schemas.submission import SubmissionReview, SubmissionResponse
from app.schemas.user import UserResponse, ClassUpdate, ClassResponse

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


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

    # 获取学生的任务完成情况
    scores_result = await db.execute(
        select(Score).where(Score.user_id == student_id)
    )
    scores = scores_result.scalars().all()

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
        "scores": scores,
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
        if score.ai_total_score:
            score.final_score = score.ai_total_score * 0.6 + review_data.teacher_score * 0.4
        else:
            score.final_score = review_data.teacher_score
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
                if score.ai_total_score:
                    score.final_score = score.ai_total_score * 0.6 + teacher_score * 0.4
                else:
                    score.final_score = teacher_score
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
        # 重新计算最终分数
        base = score.ai_total_score or score.teacher_score or 0
        score.final_score = base + (score.bonus_score or 0)
    else:
        # 全局加减分（不针对特定任务），给所有任务都加上
        scores_result = await db.execute(
            select(Score).where(Score.user_id == student_id)
        )
        scores = scores_result.scalars().all()
        for score in scores:
            score.bonus_score = (score.bonus_score or 0) + adjustment
            base = score.ai_total_score or score.teacher_score or 0
            score.final_score = base + (score.bonus_score or 0)

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
        task_count = 0

        for task in tasks:
            score = scores.get(task.id)
            if score:
                final = score.final_score or 0
                bonus = score.bonus_score or 0
                task_scores.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "ai_score": round(score.ai_total_score or 0, 1),
                    "teacher_score": round(score.teacher_score or 0, 1) if score.teacher_score else None,
                    "bonus_score": round(bonus, 1),
                    "final_score": round(final, 1),
                    "status": score.status
                })
                total_weighted += final
                total_bonus += bonus
                task_count += 1
            else:
                task_scores.append({
                    "task_id": task.id,
                    "task_title": task.title,
                    "ai_score": None,
                    "teacher_score": None,
                    "bonus_score": 0,
                    "final_score": None,
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
            "average_score": avg_score,
            "task_count": task_count
        })

    # 获取任务列表信息
    task_list = [{"id": t.id, "title": t.title} for t in tasks]

    return {"students": result, "tasks": task_list}


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
