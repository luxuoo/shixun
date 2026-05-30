from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class GradeScheme(Base):
    """成绩方案"""
    __tablename__ = "grade_schemes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)  # 关联班级（可选）
    decimal_places = Column(Integer, default=1)  # 小数位数
    is_active = Column(Boolean, default=False)  # 是否为当前启用方案
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    items = relationship("GradeItem", back_populates="scheme", cascade="all, delete-orphan")
    class_ = relationship("Class")
    creator = relationship("User")


class GradeItem(Base):
    """计分项目"""
    __tablename__ = "grade_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scheme_id = Column(Integer, ForeignKey("grade_schemes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)  # 项目名称（平时分/考试分/实训分等）
    weight = Column(Float, nullable=False)  # 权重百分比（0-100）
    max_score = Column(Float, default=100)  # 满分上限
    sort_order = Column(Integer, default=0)  # 排序
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    scheme = relationship("GradeScheme", back_populates="items")
    records = relationship("GradeRecord", back_populates="item", cascade="all, delete-orphan")


class GradeRecord(Base):
    """成绩记录"""
    __tablename__ = "grade_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("grade_items.id"), nullable=False)
    score = Column(Float, nullable=True)  # 分数（NULL表示未录入）
    remark = Column(String(200), nullable=True)  # 备注（缺考/缓考等）
    status = Column(String(20), default="normal")  # normal/absent/excused
    recorded_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    student = relationship("User", foreign_keys=[student_id])
    item = relationship("GradeItem", back_populates="records")
    recorder = relationship("User", foreign_keys=[recorded_by])
