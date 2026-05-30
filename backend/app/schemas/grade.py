from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ==================== 成绩方案 ====================

class GradeSchemeCreate(BaseModel):
    name: str
    class_id: Optional[int] = None
    decimal_places: int = 1


class GradeSchemeUpdate(BaseModel):
    name: Optional[str] = None
    class_id: Optional[int] = None
    decimal_places: Optional[int] = None


class GradeItemBase(BaseModel):
    name: str
    weight: float
    max_score: float = 100
    sort_order: int = 0


class GradeItemCreate(GradeItemBase):
    pass


class GradeItemUpdate(BaseModel):
    name: Optional[str] = None
    weight: Optional[float] = None
    max_score: Optional[float] = None
    sort_order: Optional[int] = None


class GradeItemResponse(GradeItemBase):
    id: int
    scheme_id: int

    class Config:
        from_attributes = True


class GradeSchemeResponse(BaseModel):
    id: int
    name: str
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    decimal_places: int
    is_active: bool
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    items: List[GradeItemResponse] = []
    weight_total: float = 0

    class Config:
        from_attributes = True


# ==================== 成绩记录 ====================

class GradeRecordCreate(BaseModel):
    student_id: int
    item_id: int
    score: Optional[float] = None
    remark: Optional[str] = None
    status: str = "normal"


class GradeRecordUpdate(BaseModel):
    score: Optional[float] = None
    remark: Optional[str] = None
    status: Optional[str] = None


class GradeRecordResponse(BaseModel):
    id: int
    student_id: int
    item_id: int
    score: Optional[float] = None
    remark: Optional[str] = None
    status: str
    recorded_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GradeRecordBatch(BaseModel):
    records: List[GradeRecordCreate]


# ==================== 成绩汇总 ====================

class StudentGradeItem(BaseModel):
    item_id: int
    item_name: str
    weight: float
    max_score: float
    score: Optional[float] = None
    remark: Optional[str] = None
    status: str = "normal"


class StudentGradeResponse(BaseModel):
    student_id: int
    student_no: str
    student_name: str
    class_name: str
    items: List[StudentGradeItem] = []
    total_score: Optional[float] = None
    decimal_places: int = 1


class GradeStatistics(BaseModel):
    item_name: str
    count: int
    avg: float
    max: float
    min: float
    pass_rate: float  # 及格率（>=60%）
