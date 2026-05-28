from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("task_steps.id"), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(20), default="python")
    status = Column(String(20), default="pending")  # pending/ai_scored/reviewed
    ai_score = Column(Float)
    ai_feedback = Column(Text)
    teacher_score = Column(Float)
    teacher_comment = Column(Text)
    final_score = Column(Float)
    file_attachments = Column(Text)  # JSON: 附件列表
    submitted_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)

    # 关系
    user = relationship("User", back_populates="submissions")
    task = relationship("Task", back_populates="submissions")
    step = relationship("TaskStep", back_populates="submissions")
