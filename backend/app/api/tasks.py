from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from openai import OpenAIError, APIError, AuthenticationError, APITimeoutError
from app.core.database import get_db
from app.core.security import get_current_user, get_current_teacher
from app.models.user import User
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskWithSteps,
    TaskStepCreate,
    TaskStepUpdate,
    TaskStepResponse
)
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/tasks", tags=["任务"])


@router.get("", response_model=list[TaskResponse])
async def get_tasks(
    category: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Task).where(Task.is_active == True)
    if category:
        query = query.where(Task.category == category)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskWithSteps)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Task)
        .where(Task.id == task_id)
        .options(selectinload(Task.steps))
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


@router.post("", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    task = Task(
        **task_data.model_dump(),
        created_by=current_user.id
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/{task_id}/steps", response_model=TaskStepResponse)
async def create_task_step(
    task_id: int,
    step_data: TaskStepCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # 检查任务是否存在
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    step = TaskStep(
        task_id=task_id,
        step_order=step_data.step_order,
        title=step_data.title,
        description=step_data.description,
        requirements=step_data.requirements,
        reference_code=step_data.reference_code,
        expected_output=step_data.expected_output,
        hints_available=step_data.hints_available
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return step


@router.get("/{task_id}/steps", response_model=list[TaskStepResponse])
async def get_task_steps(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(TaskStep)
        .where(TaskStep.task_id == task_id)
        .order_by(TaskStep.step_order)
    )
    return result.scalars().all()


@router.get("/{task_id}/steps/{step_id}", response_model=TaskStepResponse)
async def get_task_step(
    task_id: int,
    step_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(TaskStep)
        .where(TaskStep.task_id == task_id, TaskStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="步骤不存在"
        )
    return step


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 先删除关联记录（外键约束）
    await db.execute(delete(AiLog).where(AiLog.task_id == task_id))
    await db.execute(delete(Score).where(Score.task_id == task_id))
    await db.execute(delete(Submission).where(Submission.task_id == task_id))
    await db.execute(delete(TaskStep).where(TaskStep.task_id == task_id))
    await db.delete(task)
    await db.commit()
    return {"message": "任务已删除"}


@router.put("/{task_id}/steps/{step_id}", response_model=TaskStepResponse)
async def update_task_step(
    task_id: int,
    step_id: int,
    step_data: TaskStepUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    update_data = step_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(step, key, value)

    await db.commit()
    await db.refresh(step)
    return step


@router.delete("/{task_id}/steps/{step_id}")
async def delete_task_step(
    task_id: int,
    step_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    result = await db.execute(
        select(TaskStep).where(TaskStep.task_id == task_id, TaskStep.id == step_id)
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=404, detail="步骤不存在")

    await db.delete(step)
    await db.commit()
    return {"message": "步骤已删除"}


@router.post("/ai-decompose")
async def ai_decompose_task(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """AI 自动分解实训任务并可直接发布"""
    title = data.get("title", "")
    description = data.get("description", "")
    category = data.get("category", "")
    difficulty = data.get("difficulty", 3)
    auto_publish = data.get("auto_publish", False)
    detail_level = data.get("detail_level", "normal")
    steps_count = data.get("steps_count", 0)

    if not title or not description:
        raise HTTPException(status_code=400, detail="请提供任务名称和描述")

    # 调用 AI 分解任务
    try:
        result = await ai_service.decompose_task(
            title=title,
            description=description,
            category=category,
            difficulty=difficulty,
            detail_level=detail_level,
            steps_count=steps_count
        )
    except AuthenticationError:
        raise HTTPException(status_code=502, detail="AI 服务认证失败，请联系管理员检查 API Key 配置")
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="AI 服务响应超时，请稍后重试")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"AI 服务返回错误：{str(e)[:200]}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI 服务不可用：{str(e)[:200]}")

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "AI 分解失败"))

    task_data = result["data"]

    # 如果选择自动发布，直接创建任务和步骤
    if auto_publish:
        task = Task(
            title=task_data.get("title", title),
            description=task_data.get("description", description),
            category=task_data.get("category", category),
            difficulty=task_data.get("difficulty", difficulty),
            total_steps=len(task_data.get("steps", [])),
            estimated_hours=task_data.get("estimated_hours"),
            created_by=current_user.id,
            is_active=True
        )
        db.add(task)
        await db.flush()

        for step_data in task_data.get("steps", []):
            step = TaskStep(
                task_id=task.id,
                step_order=step_data.get("step_order", 1),
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                requirements=step_data.get("requirements", ""),
                expected_output=step_data.get("expected_output", ""),
                hints_available=step_data.get("hints_available", 3)
            )
            db.add(step)

        await db.commit()
        await db.refresh(task)

        return {
            "success": True,
            "published": True,
            "task_id": task.id,
            "message": f"任务已创建并发布，共 {len(task_data.get('steps', []))} 个步骤",
            "data": task_data,
            "tokens_used": result["tokens_used"]
        }

    # 仅返回分解结果，不发布
    return {
        "success": True,
        "published": False,
        "data": task_data,
        "tokens_used": result["tokens_used"]
    }
