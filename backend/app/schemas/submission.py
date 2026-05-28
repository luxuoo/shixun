from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SubmissionBase(BaseModel):
    task_id: int
    step_id: int
    code: str
    language: str = "python"


class SubmissionCreate(SubmissionBase):
    file_attachments: Optional[List[str]] = None


class SubmissionResponse(SubmissionBase):
    id: int
    user_id: int
    status: str
    ai_score: Optional[float] = None
    ai_feedback: Optional[str] = None
    teacher_score: Optional[float] = None
    teacher_comment: Optional[str] = None
    final_score: Optional[float] = None
    file_attachments: Optional[str] = None
    submitted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    # 关联信息（教师查看用）
    user_name: Optional[str] = None
    username: Optional[str] = None
    task_title: Optional[str] = None
    step_title: Optional[str] = None

    class Config:
        from_attributes = True


class SubmissionReview(BaseModel):
    teacher_score: float
    teacher_comment: Optional[str] = None


class AiHintRequest(BaseModel):
    task_id: int
    step_id: int
    student_code: Optional[str] = None
    question: Optional[str] = None


class AiHintResponse(BaseModel):
    hint_level: int
    content: str
    remaining_hints: int


class AiAnalyzeRequest(BaseModel):
    task_id: int
    step_id: int
    code: str


class AiAnalyzeResponse(BaseModel):
    analysis: str
    suggestions: List[str]


class AiScoreRequest(BaseModel):
    task_id: int
    step_id: int
    code: str


class AiScoreResponse(BaseModel):
    total_score: float
    correctness: float
    code_style: float
    completion: float
    creativity: float
    feedback: str
    suggestions: List[str]


class ScoreResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    ai_total_score: Optional[float] = None
    completion_rate: Optional[float] = None
    teacher_score: Optional[float] = None
    final_score: Optional[float] = None
    ai_hint_count: Optional[int] = None
    total_submissions: Optional[int] = None
    status: str
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    # 关联信息
    user_name: Optional[str] = None
    username: Optional[str] = None
    task_title: Optional[str] = None

    class Config:
        from_attributes = True


class AiLogResponse(BaseModel):
    id: int
    user_id: int
    task_id: Optional[int] = None
    step_id: Optional[int] = None
    request_type: Optional[str] = None
    hint_level: Optional[int] = None
    request_content: Optional[str] = None
    response_content: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: Optional[datetime] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True
