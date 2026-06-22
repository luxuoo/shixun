"""过程性评价数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class EvalTemplate(Base):
    """评价方案模板"""
    __tablename__ = "eval_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    is_active = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    phases = relationship("EvalPhase", back_populates="template", cascade="all, delete-orphan", order_by="EvalPhase.sort_order")
    class_ = relationship("Class")
    creator = relationship("User")


class EvalPhase(Base):
    """评价阶段（课前/课中/课后）"""
    __tablename__ = "eval_phases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("eval_templates.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)  # 课前/课中/课后
    weight = Column(Float, nullable=False, default=0)  # 权重百分比
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    template = relationship("EvalTemplate", back_populates="phases")
    indicators = relationship("EvalIndicator", back_populates="phase", cascade="all, delete-orphan", order_by="EvalIndicator.sort_order")


class EvalIndicator(Base):
    """评价指标/评分项"""
    __tablename__ = "eval_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phase_id = Column(Integer, ForeignKey("eval_phases.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)  # 指标名称
    weight = Column(Float, nullable=False, default=0)  # 在阶段内的权重百分比
    max_score = Column(Float, default=100)  # 满分上限
    score_type = Column(String(20), default="value")  # value/grade/percent
    capability_dim = Column(String(30), nullable=False, default="knowledge")  # knowledge/skill/quality/innovation
    data_source = Column(String(30), default="manual")  # manual/submission/attendance/ai_score/api
    auto_collect = Column(Boolean, default=False)  # 是否自动采集
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    phase = relationship("EvalPhase", back_populates="indicators")
    scorer_configs = relationship("EvalScorerConfig", back_populates="indicator", cascade="all, delete-orphan")
    records = relationship("EvalRecord", back_populates="indicator")


class EvalScorerConfig(Base):
    """评分主体配置"""
    __tablename__ = "eval_scorer_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    indicator_id = Column(Integer, ForeignKey("eval_indicators.id", ondelete="CASCADE"), nullable=False)
    scorer_role = Column(String(20), nullable=False)  # student(self-eval)/teacher/mentor/peer
    weight = Column(Float, nullable=False, default=100)  # 该主体的评分占比

    # 关系
    indicator = relationship("EvalIndicator", back_populates="scorer_configs")


class EvalRecord(Base):
    """评价记录 — 每条得分可溯源"""
    __tablename__ = "eval_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("eval_indicators.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("eval_templates.id"), nullable=False)
    score = Column(Float, nullable=True)  # 得分
    scorer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 评分人
    scorer_role = Column(String(20), nullable=True)  # student/teacher/mentor/peer/system
    evidence_type = Column(String(30), nullable=True)  # submission/attendance/ai_score/manual
    evidence_id = Column(Integer, nullable=True)  # 关联的原始记录ID
    remark = Column(String(200), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    student = relationship("User", foreign_keys=[student_id])
    scorer = relationship("User", foreign_keys=[scorer_id])
    indicator = relationship("EvalIndicator", back_populates="records")


class EvalSnapshot(Base):
    """评价快照 — 用于趋势追踪"""
    __tablename__ = "eval_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("eval_templates.id"), nullable=False)
    total_score = Column(Float)
    phase_scores = Column(Text)  # JSON: {"课前": 85, "课中": 90, "课后": 88}
    dim_scores = Column(Text)  # JSON: {"knowledge": 85, "skill": 90, "quality": 88, "innovation": 75}
    snapshot_date = Column(DateTime, server_default=func.now())

    # 关系
    student = relationship("User")
