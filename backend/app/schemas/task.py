from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskStepBase(BaseModel):
    step_order: int
    title: str
    description: Optional[str] = None
    requirements: Optional[str] = None
    reference_code: Optional[str] = None
    expected_output: Optional[str] = None
    hints_available: int = 3


class TaskStepCreate(TaskStepBase):
    pass


class TaskStepUpdate(BaseModel):
    step_order: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    reference_code: Optional[str] = None
    expected_output: Optional[str] = None
    hints_available: Optional[int] = None


class TaskStepResponse(TaskStepBase):
    id: int
    task_id: int

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: int = 1
    total_steps: int
    estimated_hours: Optional[float] = None
    cover_image: Optional[str] = None
    is_active: bool = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[int] = None
    total_steps: Optional[int] = None
    estimated_hours: Optional[float] = None
    cover_image: Optional[str] = None
    is_active: Optional[bool] = None


class TaskResponse(TaskBase):
    id: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskWithSteps(TaskResponse):
    steps: List[TaskStepResponse] = []


class TaskWithProgress(TaskResponse):
    """任务+学生进度（用于学生端）"""
    completed_steps: int = 0
    total_submissions: int = 0
    final_score: Optional[float] = None
    progress_status: str = "not_started"  # not_started/in_progress/completed
