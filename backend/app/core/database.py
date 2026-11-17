from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
import asyncio
import logging
import os
from pathlib import Path

# 确保数据目录存在
db_path = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
db_dir = os.path.dirname(db_path)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

# SQL 日志默认关闭：echo=True 会把每条语句打到 stdout，既吵又慢
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    # 后台 AI 评分与用户请求可能同时写 SQLite，给锁等待留出时间
    connect_args={"timeout": 30} if settings.DATABASE_URL.startswith("sqlite") else {}
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


# 表结构演进交给 Alembic（backend/alembic/），不再启动时 ALTER 补列 / 补索引。
# 索引已声明进 models 的 metadata，随基线迁移一起创建。


def _alembic_config():
    from alembic.config import Config

    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    return cfg


def _run_migrations():
    """新库 upgrade 建表；老库 stamp 基线后补齐新增表（只建缺失、不改已有）"""
    from alembic import command
    from sqlalchemy import create_engine, inspect

    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "")
    cfg = _alembic_config()
    eng = create_engine(sync_url)
    try:
        insp = inspect(eng)
        versioned = insp.has_table("alembic_version")
        legacy = insp.has_table("users")
    finally:
        eng.dispose()

    if not versioned and legacy:
        command.stamp(cfg, "head")
        bridge = create_engine(sync_url)
        try:
            Base.metadata.create_all(bind=bridge, checkfirst=True)
        finally:
            bridge.dispose()
        logger.info("老库已 stamp 到 Alembic 基线并补齐新增表")
    else:
        command.upgrade(cfg, "head")


async def init_db():
    # SQLite 用 WAL 模式：读不阻塞写，减少后台评分与页面请求并发时的锁冲突
    if settings.DATABASE_URL.startswith("sqlite"):
        async with engine.begin() as conn:
            try:
                await conn.execute(text("PRAGMA journal_mode=WAL"))
                await conn.execute(text("PRAGMA synchronous=NORMAL"))
            except Exception as e:
                logger.debug("WAL 设置失败: %s", e)
    # 迁移是同步阻塞动作，放线程里跑，避免卡住事件循环
    await asyncio.to_thread(_run_migrations)
