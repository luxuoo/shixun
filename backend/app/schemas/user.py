from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: str = "student"
    class_id: Optional[int] = None
    student_id: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    class_id: Optional[int] = None
    student_id: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class ClassBase(BaseModel):
    name: str
    description: Optional[str] = None


class ClassCreate(ClassBase):
    teacher_id: Optional[int] = None


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    teacher_id: Optional[int] = None


class ClassResponse(ClassBase):
    id: int
    teacher_id: Optional[int] = None
    created_at: Optional[datetime] = None
    teacher_name: Optional[str] = None
    student_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
