from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class AppSetting(Base):
    """运行时 KV 配置（管理员后台可改，优先于 .env）

    目前用于 AI 服务商连接信息（api_key / api_url / model / 默认服务商）。
    key 约定：ai.<provider>.<field>，如 ai.deepseek.api_key、ai.provider。
    value 一律存字符串；存了空字符串表示「显式置空」（不回退 .env）。
    """
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(2000), default="")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    updated_by = Column(Integer)  # 最后修改人 user id
