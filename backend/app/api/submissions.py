import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    ScoreResponse
)
from app.services.ai_service import ai_service
from app.api.auth import _system_settings

router = APIRouter(prefix="/api/submissions", tags=["提交"])


async def _auto_score_background(
    user_id: int,
    task_id: int,
    step_id: int,
    code: str,
    step_requirements: str,
    task_title: str,
    step_title: str
):
    """后台自动 AI 评分任务"""
    from app.core.database import async_session
    async with async_session() as db:
        try:
            ai_result = await ai_service.score_submission(
                code=code,
                step_requirements=step_requirements,
                task_title=task_title,
                step_title=step_title
            )

            # 更新提交记录
            sub_result = await db.execute(
                select(Submission)
                .where(Submission.user_id == user_id, Submission.task_id == task_id, Submission.step_id == step_id)
                .order_by(Submission.submitted_at.desc())
                .limit(1)
            )
            submission = sub_result.scalar_one_or_none()
            if submission:
                submission.ai_score = ai_result["total_score"]
                submission.ai_feedback = ai_result["feedback"]
                submission.status = "ai_scored"

            # 记录 AI 日志
            ai_log = AiLog(
                user_id=user_id, task_id=task_id, step_id=step_id,
                request_type="score",
                request_content=code[:500],
                response_content=str(ai_result)[:1000],
                tokens_used=ai_result.get("tokens_used", 0)
            )
            db.add(ai_log)

            # 更新评分记录
            score_result = await db.execute(
                select(Score).where(Score.user_id == user_id, Score.task_id == task_id)
            )
            score = score_result.scalar_one_or_none()
            if score:
                all_scores_result = await db.execute(
                    select(func.avg(Submission.ai_score))
                    .where(Submission.user_id == user_id, Submission.task_id == task_id, Submission.ai_score.isnot(None))
                )
                avg_score = all_scores_result.scalar()
                score.ai_total_score = avg_score if avg_score else ai_result["total_score"]

                total_steps_result = await db.execute(select(func.count(TaskStep.id)).where(TaskStep.task_id == task_id))
                total_steps = total_steps_result.scalar() or 1

                completed_steps_result = await db.execute(
                    select(func.count(func.distinct(Submission.step_id)))
                    .where(Submission.user_id == user_id, Submission.task_id == task_id, Submission.ai_score.isnot(None), Submission.ai_score >= 60)
                )
                completed_steps = completed_steps_result.scalar() or 0
                score.completion_rate = (completed_steps / total_steps) * 100

                if score.teacher_score:
                    score.final_score = (score.ai_total_score * 0.6 + score.teacher_score * 0.4)
                else:
                    score.final_score = score.ai_total_score

            await db.commit()
        except Exception as e:
            print(f"后台 AI 评分失败: {e}")


@router.post("", response_model=SubmissionResponse)
async def create_submission(
    submission_data: SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 验证任务和步骤存在
    task_result = await db.execute(select(Task).where(Task.id == submission_data.task_id))
    task = task_result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    step_result = await db.execute(
        select(TaskStep).where(
            TaskStep.task_id == submission_data.task_id,
            TaskStep.id == submission_data.step_id
        )
    )
    step = step_result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    # 创建提交记录
    submission = Submission(
        user_id=current_user.id,
        task_id=submission_data.task_id,
        step_id=submission_data.step_id,
        code=submission_data.code,
        language=submission_data.language,
        file_attachments=str(submission_data.file_attachments) if submission_data.file_attachments else None
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    # 更新或创建评分记录
    score_result = await db.execute(
        select(Score).where(Score.user_id == current_user.id, Score.task_id == submission_data.task_id)
    )
    score = score_result.scalar_one_or_none()
    if not score:
        score = Score(user_id=current_user.id, task_id=submission_data.task_id, total_submissions=1)
        db.add(score)
    else:
        score.total_submissions = (score.total_submissions or 0) + 1
    await db.commit()

    # 后台自动 AI 评分（不阻塞响应，受设置控制）
    if _system_settings.get("ai_auto_score", True):
        background_tasks.add_task(
            _auto_score_background,
            user_id=current_user.id,
            task_id=submission_data.task_id,
            step_id=submission_data.step_id,
            code=submission_data.code,
            step_requirements=step.requirements or "",
            task_title=task.title,
            step_title=step.title
        )

    return submission


@router.get("", response_model=list[SubmissionResponse])
async def get_submissions(
    task_id: int = None,
    step_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Submission).where(Submission.user_id == current_user.id)
    if task_id:
        query = query.where(Submission.task_id == task_id)
    if step_id:
        query = query.where(Submission.step_id == step_id)
    query = query.order_by(Submission.submitted_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(
    submission_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Submission).where(Submission.id == submission_id)
    )
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="提交记录不存在")

    # 学生只能查看自己的提交
    if current_user.role == "student" and submission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")

    return submission


@router.get("/scores/my", response_model=list[ScoreResponse])
async def get_my_scores(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前学生的成绩单"""
    scores_result = await db.execute(
        select(Score).where(Score.user_id == current_user.id)
    )
    scores = scores_result.scalars().all()

    result = []
    for score in scores:
        task_result = await db.execute(select(Task.title).where(Task.id == score.task_id))
        task_title = task_result.scalar()
        result.append(ScoreResponse(
            id=score.id,
            user_id=score.user_id,
            task_id=score.task_id,
            ai_total_score=score.ai_total_score,
            completion_rate=score.completion_rate,
            teacher_score=score.teacher_score,
            final_score=score.final_score,
            ai_hint_count=score.ai_hint_count,
            total_submissions=score.total_submissions,
            status=score.status,
            completed_at=score.completed_at,
            reviewed_at=score.reviewed_at,
            user_name=current_user.name,
            username=current_user.username,
            task_title=task_title
        ))
    return result
