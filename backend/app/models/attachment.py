from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class Attachment(Base):
    """正式附件表：替代 submissions.file_attachments 的 JSON 字符串存储。

    落盘文件用 uuid 命名，原始文件名仅做展示；url 指向 /uploads 静态目录。
    有了独立行记录，按用户/提交查询附件、清理孤儿文件都变成普通 SQL。
    """

    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)      # 原始文件名（展示用）
    stored_name = Column(String(255), nullable=False)   # 落盘文件名（uuid，防路径穿越）
    url = Column(String(500), nullable=False)           # /uploads/attachments/<stored_name>
    size = Column(Integer, default=0)
    content_type = Column(String(100), default="")
    created_at = Column(DateTime, server_default=func.now())