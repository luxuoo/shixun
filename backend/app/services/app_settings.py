"""运行时应用配置：管理员后台可改，数据库优先于 .env

为什么单独一层：
- settings（pydantic）只在启动时从 .env 读一次，改一次密钥要登服务器改文件 + 重启；
- ai_service 里的取配置路径是同步代码，而数据库是异步引擎，
  所以把 DB 里的覆盖值在「启动时 / 保存时」加载进进程内缓存，同步直接读。

多 worker 一致性（关键）：
- 生产环境 uvicorn --workers 2 起了两个进程，各有一份缓存；
  保存请求只会刷新处理它的那个 worker，另一个进程会继续用旧配置。
- 解决：保存方在 commit 后写一个「时间戳戳记文件」（与数据库同目录）；
  其他 worker 每次读配置前对比戳记，发现变化就用 sqlite3 同步重读一遍覆盖值。
  戳记读取只是一次本地小文件 open，开销可忽略。

key 约定（存 app_settings 表）：
  ai.provider          当前默认服务商（mimo / deepseek）
  ai.<provider>.api_key / .api_url / .model

语义：DB 里「存在该 key」即覆盖（含空字符串 = 显式置空）；
      DB 里没有该 key 则回退 .env 的值。
"""
import os
import sqlite3
import time
from typing import Optional
from urllib.parse import unquote

from sqlalchemy import select

from app.core.config import settings as env_settings

PROVIDERS = ("mimo", "deepseek")
_FIELDS = ("api_key", "api_url", "model")

# 进程内覆盖缓存：{"ai.deepseek.api_key": "sk-xxx", ...}
_overrides: dict[str, str] = {}
_loaded_stamp: float = 0.0


def _valid_key(key: str) -> bool:
    if key == "ai.provider":
        return True
    if not key.startswith("ai."):
        return False
    parts = key.split(".")
    return len(parts) == 3 and parts[1] in PROVIDERS and parts[2] in _FIELDS


# ---------------- 跨 worker 同步：戳记文件 ----------------

def _sqlite_path(url: str) -> Optional[str]:
    """从 DATABASE_URL 解析 SQLite 文件路径；非 SQLite 返回 None"""
    if "sqlite" not in (url or ""):
        return None
    if ":///" not in url:
        return None
    rest = url.split(":///", 1)[1]
    rest = rest.split("?", 1)[0]
    rest = unquote(rest)
    return rest or None


_DB_PATH = _sqlite_path(env_settings.DATABASE_URL)
_STAMP_PATH = (os.path.join(os.path.dirname(_DB_PATH), ".app_settings.stamp")
               if _DB_PATH else None)


def _read_stamp() -> float:
    """读戳记（其他 worker 最后一次保存的时间戳）；读不到返回 0"""
    if not _STAMP_PATH:
        return 0.0
    try:
        with open(_STAMP_PATH, "r", encoding="utf-8") as f:
            return float(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0.0


def _write_stamp() -> None:
    """保存方调用：写入新戳记并记下本进程已同步到该版本"""
    global _loaded_stamp
    stamp = time.time()
    if _STAMP_PATH:
        try:
            os.makedirs(os.path.dirname(_STAMP_PATH), exist_ok=True)
            with open(_STAMP_PATH, "w", encoding="utf-8") as f:
                f.write(str(stamp))
        except OSError:
            pass  # 写不了戳记只是失去跨进程即时性，下次重启仍会加载
    _loaded_stamp = stamp


def _sync_read_overrides() -> Optional[dict]:
    """用 sqlite3 同步读一遍覆盖值（只读连接，不碰异步引擎）"""
    if not _DB_PATH:
        return None
    try:
        conn = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True, timeout=2)
        try:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        finally:
            conn.close()
        return {k: (v or "") for k, v in rows if _valid_key(k)}
    except sqlite3.Error:
        # 表还不存在 / 文件被锁：保留现有缓存
        return None


def _maybe_refresh() -> None:
    """读配置前的钩子：戳记有变化（别的 worker 保存过）则同步刷新本进程缓存"""
    global _overrides, _loaded_stamp
    stamp = _read_stamp()
    if not stamp or stamp == _loaded_stamp:
        return
    fresh = _sync_read_overrides()
    if fresh is not None:
        _overrides = fresh
        _loaded_stamp = stamp


# ---------------- 读写接口 ----------------

async def reload() -> None:
    """从数据库重新加载覆盖值（启动时与每次保存后调用）"""
    global _overrides
    from app.core.database import async_session
    from app.models.app_setting import AppSetting

    async with async_session() as db:
        result = await db.execute(select(AppSetting))
        _overrides = {row.key: (row.value or "") for row in result.scalars() if _valid_key(row.key)}
    # 本进程刚从库里读出了最新值，写个戳记让其他 worker 也跟上
    _write_stamp()


async def set_values(items: dict[str, Optional[str]], updated_by: int) -> None:
    """写入覆盖值并刷新缓存

    items 里 value 为 None 表示「删除该 key」（回退 .env）；
    为字符串（含空串）表示覆盖。
    """
    from sqlalchemy import delete
    from app.core.database import async_session
    from app.models.app_setting import AppSetting

    async with async_session() as db:
        for key, value in items.items():
            if not _valid_key(key):
                raise ValueError(f"不支持的配置项：{key}")
            if value is None:
                await db.execute(delete(AppSetting).where(AppSetting.key == key))
                _overrides.pop(key, None)
                continue
            obj = (await db.execute(select(AppSetting).where(AppSetting.key == key))).scalar_one_or_none()
            if obj is None:
                db.add(AppSetting(key=key, value=value, updated_by=updated_by))
            else:
                obj.value = value
                obj.updated_by = updated_by
        await db.commit()
    await reload()


def get_raw(key: str) -> Optional[str]:
    """取某项的覆盖值；DB 未配置返回 None"""
    _maybe_refresh()
    return _overrides.get(key)


def mask_key(key: str) -> str:
    """密钥脱敏：保留头 6 位与尾 4 位"""
    if not key:
        return ""
    if len(key) <= 12:
        return key[:2] + "****"
    return f"{key[:6]}...{key[-4:]}"


def provider_config(name: Optional[str] = None) -> dict:
    """与 Settings.provider_config 同构，但应用数据库覆盖

    返回 {name, label, api_key, api_url, model, source: {field: "db"|"env"}}
    """
    _maybe_refresh()
    base = env_settings.provider_config(name)
    conf = dict(base)
    source = {f: "env" for f in ("api_key", "api_url", "model")}
    for field in _FIELDS:
        key = f"ai.{base['name']}.{field}"
        if key in _overrides:
            conf[field] = _overrides[key]
            source[field] = "db"
    conf["source"] = source
    return conf


def default_provider() -> str:
    """数据库里选的默认服务商（未设置回退 .env 的 AI_PROVIDER）"""
    _maybe_refresh()
    value = _overrides.get("ai.provider", "").strip().lower()
    if value in PROVIDERS:
        return value
    return env_settings.provider_config()["name"]


def available_providers() -> list:
    """列出所有服务商及是否已配置密钥（含来源，供管理页展示）"""
    return [
        {
            "name": p["name"],
            "label": p["label"],
            "model": p["model"],
            "api_url": p["api_url"],
            "configured": bool(p["api_key"]),
            "key_masked": mask_key(p["api_key"]),
            "source": p["source"],
        }
        for p in (provider_config("mimo"), provider_config("deepseek"))
    ]
