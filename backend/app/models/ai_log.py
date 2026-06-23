from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AiLog(Base):
    __tablename__ = "ai_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    step_id = Column(Integer, ForeignKey("task_steps.id"))
    request_type = Column(String(20))  # hint/analyze/score/score_error
    hint_level = Column(Integer)  # 1/2/3 级提示
    request_content = Column(Text)
    response_content = Column(Text)
    tokens_used = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    user = relationship("User", back_populates="ai_logs")
    step = relationship("TaskStep", back_populates="ai_logs")


class Score(Base):
    """任务级评分记录 — AI 评分、教师评分、出勤加分等综合计算"""
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    ai_total_score = Column(Float)  # AI 总评分
    completion_rate = Column(Float)  # 完成率
    teacher_score = Column(Float)  # 老师评分
    attendance_score = Column(Float, default=0)  # 出勤加分
    bonus_score = Column(Float, default=0)  # 其他加分
    final_score = Column(Float)  # 最终综合评分
    ai_hint_count = Column(Integer)  # AI 提示使用次数
    total_submissions = Column(Integer)  # 总提交次数
    rollcall_count = Column(Integer, default=0)  # 点名出勤次数
    status = Column(String(20), default="in_progress")  # in_progress/completed/reviewed
    completed_at = Column(DateTime)
    reviewed_at = Column(DateTime)

    # 关系
    user = relationship("User", back_populates="scores")
    task = relationship("Task", back_populates="scores")


class RollcallRecord(Base):
    __tablename__ = "rollcall_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"))
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    student = relationship("User")
