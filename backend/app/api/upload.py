"""附件上传：落盘 + 落 attachments 表，返回可访问 url。

前端 FileUpload 组件 POST  multipart 到 /api/upload（字段名 file），
携带 Bearer token。磁盘文件名用 uuid，原始文件名仅展示，杜绝路径穿越；
扩展名白名单拒绝可执行/可脚本类型（.html/.svg/.exe 等），避免静态目录被当 XSS 载体。
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.attachment import Attachment
from app.models.user import User

router = APIRouter(prefix="/api", tags=["上传"])

MAX_BYTES = 20 * 1024 * 1024  # 20MB 服务端上限（组件默认提示 10MB）

_ALLOWED_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".7z", ".tar", ".gz",
    ".txt", ".md", ".csv", ".json", ".ipynb",
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".go", ".rs", ".sql",
}


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="文件超过 20MB 上限")

    original = os.path.basename(file.filename or "file")
    ext = os.path.splitext(original)[1].lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{ext or '未知'}")

    stored = uuid.uuid4().hex + ext
    subdir = Path(settings.UPLOAD_DIR) / "attachments"
    subdir.mkdir(parents=True, exist_ok=True)
    (subdir / stored).write_bytes(data)

    url = f"/uploads/attachments/{stored}"
    att = Attachment(
        user_id=current_user.id,
        filename=original[:255],
        stored_name=stored,
        url=url,
        size=len(data),
        content_type=(file.content_type or "")[:100],
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return {"id": att.id, "url": url, "name": att.filename, "size": att.size}