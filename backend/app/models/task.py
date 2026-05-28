from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # 如: YOLO, Web, Python
    difficulty = Column(Integer, default=1)  # 1-5
    total_steps = Column(Integer, nullable=False)
    estimated_hours = Column(Float)
    cover_image = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    steps = relationship("TaskStep", back_populates="task", order_by="TaskStep.step_order")
    submissions = relationship("Submission", back_populates="task")
    scores = relationship("Score", back_populates="task")


class TaskStep(Base):
    __tablename__ = "task_steps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    requirements = Column(Text)  # 本步骤要求
    reference_code = Column(Text)  # 参考代码（老师提供）
    expected_output = Column(Text)  # 预期输出描述
    hints_available = Column(Integer, default=3)  # 可用提示次数

    # 关系
    task = relationship("Task", back_populates="steps")
    submissions = relationship("Submission", back_populates="step")
    ai_logs = relationship("AiLog", back_populates="step")
