import json
import os
import random
import string
import time
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    get_current_admin
)
from app.models.user import User, Class
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserLogin,
    UserResponse,
    Token,
    ClassCreate,
    ClassResponse
)
from app.services import scoring

router = APIRouter(prefix="/api/auth", tags=["认证"])

# 系统设置（内存缓存 + data/settings.json 持久化，重启不丢失）
_DEFAULT_SETTINGS = {
    "student_register_enabled": True,
    "ai_chat_enabled": True,
    "ai_hints_limit": 0,
    "ai_auto_score": True,
    "submission_limit": 0,
    "grade_weights": dict(scoring.DEFAULT_GRADE_WEIGHTS),
    "rollcall_score": 5,
    "rollcall_auto_score": False,
    "student_view_grades": True
}

_SETTINGS_FILE = Path(__file__).resolve().parents[2] / "data" / "settings.json"


def _load_system_settings() -> dict:
    """启动时从磁盘恢复设置，缺失或损坏则用默认值"""
    merged = dict(_DEFAULT_SETTINGS)
    try:
        if _SETTINGS_FILE.exists():
            saved = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                merged.update({k: v for k, v in saved.items() if k in _DEFAULT_SETTINGS})
    except Exception as e:  # 文件损坏不应阻塞启动
        print(f"[warn] 读取系统设置失败，使用默认值: {e}")
    return merged


def save_system_settings() -> None:
    """原子写入设置文件，避免断电/并发导致文件截断"""
    try:
        _SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _SETTINGS_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(_system_settings, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, _SETTINGS_FILE)
    except Exception as e:
        print(f"[warn] 保存系统设置失败: {e}")


_system_settings = _load_system_settings()


def _generate_password(length=8):
    """生成随机密码"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# ==================== 登录失败限流 ====================
# 进程内计数，够用于单机部署；多实例部署需换成 Redis
_LOGIN_MAX_FAILS = 5
_LOGIN_LOCK_SECONDS = 300
_login_fails: dict = {}


def _login_key(username: str, ip: str) -> str:
    return f"{(username or '').strip().lower()}|{ip}"


def _login_lock_remaining(key: str) -> int:
    """剩余锁定秒数，0 表示未锁定"""
    rec = _login_fails.get(key)
    if not rec:
        return 0
    now = time.time()
    rec["times"] = [t for t in rec["times"] if now - t < _LOGIN_LOCK_SECONDS]
    if len(rec["times"]) >= _LOGIN_MAX_FAILS:
        return max(1, int(_LOGIN_LOCK_SECONDS - (now - rec["times"][0])))
    return 0


def _record_login_fail(key: str) -> None:
    if len(_login_fails) > 5000:  # 防止字典无限增长
        _login_fails.clear()
    _login_fails.setdefault(key, {"times": []})["times"].append(time.time())


def _clear_login_fail(key: str) -> None:
    _login_fails.pop(key, None)


@router.post("/login")
async def login(user_data: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else "-"
    key = _login_key(user_data.username, ip)

    # 连续失败 5 次锁 5 分钟，防暴力破解
    remain = _login_lock_remaining(key)
    if remain > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"登录失败次数过多，请 {remain} 秒后再试"
        )

    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        _record_login_fail(key)
        left = _LOGIN_MAX_FAILS - len(_login_fails.get(key, {}).get("times", []))
        tip = f"，还可尝试 {left} 次" if 0 < left <= 3 else ""
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误{tip}"
        )

    _clear_login_fail(key)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用"
        )

    user.last_login = datetime.now(timezone.utc)

    # 学生登录自动记录考勤（每天只记一次）
    if user.role == "student":
        from app.models.ai_log import LoginRecord
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        existing = await db.execute(
            select(LoginRecord).where(
                LoginRecord.user_id == user.id,
                LoginRecord.login_date == today_str
            )
        )
        if not existing.scalar_one_or_none():
            db.add(LoginRecord(user_id=user.id, login_date=today_str))

    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "class_id": user.class_id,
            "student_id": user.student_id,
            "is_active": user.is_active,
            "created_at": str(user.created_at) if user.created_at else None,
            "last_login": str(user.last_login) if user.last_login else None
        }
    }


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """学生注册（公开接口，受开关控制）"""
    if not _system_settings["student_register_enabled"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="学生注册已关闭，请联系管理员"
        )

    # 只允许学生注册
    if user_data.role and user_data.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能注册学生账号，教师账号请联系管理员"
        )

    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        email=user_data.email,
        student_id=user_data.student_id,
        class_id=user_data.class_id,
        role="student"
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/register/admin", response_model=UserResponse)
async def register_by_admin(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """管理员创建任意角色"""
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        name=user_data.name,
        email=user_data.email,
        student_id=user_data.student_id,
        class_id=user_data.class_id,
        role=user_data.role
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/batch-register")
async def batch_register_students(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """批量注册学生 - 通过学号和姓名表格"""
    students_data = data.get("students", [])
    class_id = data.get("class_id")

    if not students_data:
        raise HTTPException(status_code=400, detail="请提供学生列表")

    if not class_id:
        raise HTTPException(status_code=400, detail="请选择班级")

    # 验证班级存在
    class_result = await db.execute(select(Class).where(Class.id == class_id))
    cls = class_result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    results = []
    errors = []

    for item in students_data:
        student_id = item.get("student_id", "").strip()
        name = item.get("name", "").strip()

        if not student_id or not name:
            errors.append(f"学号或姓名为空: {item}")
            continue

        # 用户名默认为学号
        username = student_id
        # 检查用户名是否已存在
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            errors.append(f"学号 {student_id} 已存在")
            continue

        # 生成随机密码
        password = _generate_password(8)

        user = User(
            username=username,
            password_hash=get_password_hash(password),
            role="student",
            name=name,
            class_id=class_id,
            student_id=student_id,
            is_active=True
        )
        db.add(user)
        results.append({
            "student_id": student_id,
            "name": name,
            "username": username,
            "password": password
        })

    await db.commit()

    return {
        "success": len(results),
        "errors": errors,
        "students": results,
        "class_name": cls.name
    }


@router.get("/settings")
async def get_settings():
    """获取系统设置（公开）"""
    return _system_settings


@router.put("/settings")
async def update_settings(
    data: dict,
    current_user: User = Depends(get_current_admin)
):
    """更新系统设置（管理员）"""
    if "student_register_enabled" in data:
        _system_settings["student_register_enabled"] = bool(data["student_register_enabled"])
    if "ai_chat_enabled" in data:
        _system_settings["ai_chat_enabled"] = bool(data["ai_chat_enabled"])
    if "ai_hints_limit" in data:
        _system_settings["ai_hints_limit"] = max(0, int(data["ai_hints_limit"]))
    if "ai_auto_score" in data:
        _system_settings["ai_auto_score"] = bool(data["ai_auto_score"])
    if "submission_limit" in data:
        _system_settings["submission_limit"] = max(0, int(data["submission_limit"]))
    if "grade_weights" in data:
        gw = data["grade_weights"]
        if isinstance(gw, dict):
            _system_settings["grade_weights"] = scoring.normalize_weights(gw)
    if "rollcall_score" in data:
        _system_settings["rollcall_score"] = max(0, int(data["rollcall_score"]))
    if "rollcall_auto_score" in data:
        _system_settings["rollcall_auto_score"] = bool(data["rollcall_auto_score"])
    if "student_view_grades" in data:
        _system_settings["student_view_grades"] = bool(data["student_view_grades"])
    save_system_settings()
    return _system_settings


@router.post("/change-password")
async def change_password(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """自助修改密码（学生/教师/管理员通用）

    之前只能由管理员重置，学生忘记密码必须找老师；这里补上自助通道。
    """
    old_password = (data or {}).get("old_password") or ""
    new_password = (data or {}).get("new_password") or ""

    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="请填写原密码和新密码")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    if new_password == old_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码不正确")

    current_user.password_hash = get_password_hash(new_password)
    await db.commit()
    return {"message": "密码已修改，请使用新密码登录"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# 班级相关接口
@router.post("/classes", response_model=ClassResponse)
async def create_class(
    class_data: ClassCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    class_ = Class(
        name=class_data.name,
        description=class_data.description,
        teacher_id=class_data.teacher_id or current_user.id
    )
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    return class_


@router.get("/classes", response_model=list[ClassResponse])
async def get_classes(db: AsyncSession = Depends(get_db)):
    """获取班级列表"""
    result = await db.execute(select(Class))
    return result.scalars().all()


# ==================== 用户管理（管理员） ====================

@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    role: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query.order_by(User.id))
    return result.scalars().all()


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = user_data.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        user.password_hash = get_password_hash(update_data.pop("password"))
    else:
        update_data.pop("password", None)

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    await db.delete(user)
    await db.commit()
    return {"message": "用户已删除"}


@router.put("/users/{user_id}/toggle")
async def toggle_user_status(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = not user.is_active
    await db.commit()
    return {"message": f"用户已{'启用' if user.is_active else '禁用'}", "is_active": user.is_active}
