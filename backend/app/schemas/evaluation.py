"""过程性评价 Pydantic Schemas"""
from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Dict
from datetime import datetime


# ==================== 评分主体配置 ====================
class ScorerConfigBase(BaseModel):
    scorer_role: str  # student/teacher/mentor/peer
    weight: float = 100

    @field_validator("scorer_role")
    @classmethod
    def validate_role(cls, v):
        allowed = {"student", "teacher", "mentor", "peer", "ai", "self", "enterprise"}
        if v not in allowed:
            raise ValueError(f"评分主体必须是 {allowed} 之一")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("权重必须在 0-100 之间")
        return v


class ScorerConfigCreate(ScorerConfigBase):
    pass


class ScorerConfigResponse(ScorerConfigBase):
    id: int
    indicator_id: int

    class Config:
        from_attributes = True


# ==================== 评价指标 ====================
class IndicatorBase(BaseModel):
    name: str
    weight: float
    max_score: float = 100
    score_type: str = "value"  # value/grade/percent
    capability_dim: str = "knowledge"  # knowledge/skill/quality/innovation
    data_source: str = "manual"  # manual/submission/attendance/ai_score/api
    auto_collect: bool = False
    sort_order: int = 0

    @field_validator("score_type")
    @classmethod
    def validate_score_type(cls, v):
        allowed = {"value", "grade", "percent"}
        if v not in allowed:
            raise ValueError(f"计分方式必须是 {allowed} 之一")
        return v

    @field_validator("capability_dim")
    @classmethod
    def validate_dim(cls, v):
        allowed = {"knowledge", "skill", "quality", "innovation"}
        if v not in allowed:
            raise ValueError(f"能力维度必须是 {allowed} 之一")
        return v

    @field_validator("data_source")
    @classmethod
    def validate_source(cls, v):
        allowed = {"manual", "submission", "attendance", "ai_score", "api"}
        if v not in allowed:
            raise ValueError(f"数据来源必须是 {allowed} 之一")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("权重必须在 0-100 之间")
        return v


class IndicatorCreate(IndicatorBase):
    scorer_configs: Optional[List[ScorerConfigCreate]] = None


class IndicatorUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    max_score: Optional[float] = None
    score_type: Optional[str] = None
    capability_dim: Optional[str] = None
    data_source: Optional[str] = None
    auto_collect: Optional[bool] = None
    sort_order: Optional[int] = None


class IndicatorResponse(IndicatorBase):
    id: int
    phase_id: int
    scorer_configs: List[ScorerConfigResponse] = []

    class Config:
        from_attributes = True


# ==================== 评价阶段 ====================
class PhaseBase(BaseModel):
    name: str
    weight: float
    sort_order: int = 0

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("权重必须在 0-100 之间")
        return v


class PhaseCreate(PhaseBase):
    pass


class PhaseUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    sort_order: Optional[int] = None


class PhaseResponse(PhaseBase):
    id: int
    template_id: int
    indicators: List[IndicatorResponse] = []

    class Config:
        from_attributes = True


# ==================== 评价方案模板 ====================
class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    class_id: Optional[int] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    class_id: Optional[int] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: int
    is_active: bool
    version: int
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    phases: List[PhaseResponse] = []

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    class_id: Optional[int] = None
    is_active: bool
    version: int
    phase_count: Optional[int] = 0
    indicator_count: Optional[int] = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 评价记录 ====================
class RecordBase(BaseModel):
    student_id: int
    indicator_id: int
    template_id: int
    score: Optional[float] = None
    scorer_role: str = "teacher"
    evidence_type: Optional[str] = None
    evidence_id: Optional[int] = None
    remark: Optional[str] = None


class RecordCreate(RecordBase):
    pass


class RecordBatchCreate(BaseModel):
    """批量录入"""
    template_id: int
    indicator_id: int
    records: List[Dict]  # [{student_id, score, remark}]


class RecordResponse(RecordBase):
    id: int
    scorer_id: Optional[int] = None
    created_at: Optional[datetime] = None
    # 关联信息
    student_name: Optional[str] = None
    indicator_name: Optional[str] = None
    phase_name: Optional[str] = None

    class Config:
        from_attributes = True


# ==================== 看板数据 ====================
class PhaseScoreItem(BaseModel):
    phase_id: int
    phase_name: str
    phase_weight: float
    score: float
    weighted_score: float
    indicators: List[Dict] = []  # [{name, score, max_score, weight}]


class DimScoreItem(BaseModel):
    dimension: str
    dim_label: str
    score: float
    count: int


class StudentDashboard(BaseModel):
    """学生个人看板"""
    student_id: int
    student_name: str
    template_id: int
    template_name: str
    total_score: float
    phase_scores: List[PhaseScoreItem]
    dim_scores: List[DimScoreItem]
    snapshot_date: Optional[datetime] = None


class TrendPoint(BaseModel):
    date: str
    total_score: float
    phase_scores: Dict[str, float] = {}
    dim_scores: Dict[str, float] = {}


class StudentTrend(BaseModel):
    """学生趋势数据"""
    student_id: int
    points: List[TrendPoint]


class ClassDistribution(BaseModel):
    """班级分布"""
    score_ranges: List[Dict]  # [{range: "90-100", count: 5}]
    total_students: int
    average_score: float
    pass_rate: float
    excellent_rate: float


class ClassRankingItem(BaseModel):
    rank: int
    student_id: int
    student_name: str
    total_score: float
    change: float = 0  # 进步幅度


class ClassDashboard(BaseModel):
    """班级看板"""
    class_id: int
    class_name: str
    template_id: int
    distribution: ClassDistribution
    ranking: List[ClassRankingItem]
    weak_dims: List[Dict]  # [{dimension, avg_score, label}]


# ==================== 权重校验 ====================
class WeightValidation(BaseModel):
    valid: bool
    total_weight: float
    message: str
