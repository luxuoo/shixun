from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String)
    teacher_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    teacher = relationship("User", back_populates="taught_classes", foreign_keys=[teacher_id])
    students = relationship("User", back_populates="class_", foreign_keys="User.class_id")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="student")  # student/teacher/admin
    name = Column(String(100))
    class_id = Column(Integer, ForeignKey("classes.id"))
    student_id = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime)

    # 关系
    class_ = relationship("Class", back_populates="students", foreign_keys=[class_id])
    taught_classes = relationship("Class", back_populates="teacher", foreign_keys="Class.teacher_id")
    submissions = relationship("Submission", back_populates="user")
    ai_logs = relationship("AiLog", back_populates="user")
    scores = relationship("Score", back_populates="user")
