from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.core.config import settings
import logging
import os

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


# 高频查询字段索引（表已存在时 create_all 不会补索引，这里显式补齐）
_INDEXES = [
    ("idx_ai_logs_user", "ai_logs", "user_id"),
    ("idx_ai_logs_task", "ai_logs", "task_id"),
    ("idx_ai_logs_step_lookup", "ai_logs", "user_id, task_id, step_id, request_type"),
    ("idx_ai_logs_created", "ai_logs", "created_at"),
    ("idx_sub_user", "submissions", "user_id"),
    ("idx_sub_task", "submissions", "task_id"),
    ("idx_sub_step", "submissions", "step_id"),
    ("idx_sub_user_task", "submissions", "user_id, task_id"),
    ("idx_sub_submitted", "submissions", "submitted_at"),
    ("idx_scores_user_task", "scores", "user_id, task_id"),
    ("idx_rollcall_class", "rollcall_records", "class_id"),
    ("idx_rollcall_student", "rollcall_records", "student_id"),
    ("idx_login_user", "login_records", "user_id"),
    ("idx_steps_task", "task_steps", "task_id"),
    ("idx_users_class", "users", "class_id"),
    ("idx_users_role", "users", "role"),
    ("idx_eval_records_student", "eval_records", "student_id"),
    ("idx_eval_records_indicator", "eval_records", "indicator_id"),
    ("idx_eval_records_template", "eval_records", "template_id"),
    ("idx_eval_snap_student", "eval_snapshots", "student_id, template_id"),
    ("idx_eval_phase_template", "eval_phases", "template_id"),
    ("idx_eval_indicator_phase", "eval_indicators", "phase_id"),
]


async def _ensure_indexes(conn):
    """为已存在的表补建索引（幂等，SQLite 支持 IF NOT EXISTS）"""
    for name, table, cols in _INDEXES:
        try:
            await conn.execute(text(f'CREATE INDEX IF NOT EXISTS {name} ON {table} ({cols})'))
        except Exception as e:
            # 表不存在或字段不匹配时跳过，不影响启动
            logger.debug("跳过索引 %s: %s", name, e)


def _column_ddl(col) -> str:
    """把模型列翻译成 SQLite 的 ADD COLUMN 片段（类型 + 默认值）"""
    from sqlalchemy.dialects import sqlite as sqlite_dialect

    type_sql = col.type.compile(dialect=sqlite_dialect.dialect())
    ddl = f'"{col.name}" {type_sql}'

    default = col.default
    if default is not None and getattr(default, "is_scalar", False):
        val = default.arg
        if isinstance(val, bool):
            ddl += f" DEFAULT {1 if val else 0}"
        elif isinstance(val, (int, float)):
            ddl += f" DEFAULT {val}"
        elif isinstance(val, str):
            ddl += " DEFAULT '{}'".format(val.replace("'", "''"))
    return ddl


async def _ensure_columns(conn):
    """表已存在但模型新增了字段时自动补列

    之前 scores 表缺 attendance_score/bonus_score/rollcall_count，
    点名加分一执行就报 no such column；SQLite 不能自动迁移，这里补上。
    """
    for table in Base.metadata.tables.values():
        try:
            result = await conn.execute(text(f"PRAGMA table_info({table.name})"))
            existing = {row[1] for row in result.fetchall()}
        except Exception:
            continue
        if not existing:
            continue  # 表还没建出来，交给 create 流程
        for col in table.columns:
            if col.name in existing:
                continue
            try:
                await conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {_column_ddl(col)}'))
                logger.warning("已为 %s 补充缺失字段 %s", table.name, col.name)
            except Exception as e:
                logger.warning("补字段失败 %s.%s: %s", table.name, col.name, e)


async def init_db():
    async with engine.begin() as conn:
        # 逐表创建，跳过已存在且结构不一致的表
        for table in Base.metadata.sorted_tables:
            try:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(sync_conn, checkfirst=True)
                )
            except Exception as e:
                # 表已存在但结构不同，跳过（SQLite 不支持完整 ALTER）
                logging.warning(f"跳过表 {table.name}: {e}")
        # SQLite 用 WAL 模式：读不阻塞写，减少后台评分与页面请求并发时的锁冲突
        if settings.DATABASE_URL.startswith("sqlite"):
            try:
                await conn.execute(text("PRAGMA journal_mode=WAL"))
                await conn.execute(text("PRAGMA synchronous=NORMAL"))
            except Exception as e:
                logger.debug("WAL 设置失败: %s", e)
        # 老库补字段（模型加了列但库里没有）
        await _ensure_columns(conn)
        # 补索引，加速日志 / 提交 / 评价类高频查询
        await _ensure_indexes(conn)
