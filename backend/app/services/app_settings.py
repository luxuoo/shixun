"""运行时应用配置：管理员后台可改，数据库优先于 .env

为什么单独一层：
- settings（pydantic）只在启动时从 .env 读一次，改一次密钥要登服务器改文件 + 重启；
- ai_service 里的取配置路径是同步代码，而数据库是异步引擎，
  所以把 DB 里的覆盖值在「启动时 / 保存时」加载进进程内缓存，同步直接读。

key 约定（存 app_settings 表）：
  ai.provider          当前默认服务商（mimo / deepseek）
  ai.<provider>.api_key / .api_url / .model

语义：DB 里「存在该 key」即覆盖（含空字符串 = 显式置空）；
      DB 里没有该 key 则回退 .env 的值。
"""
from typing import Optional

from sqlalchemy import select

from app.core.config import settings as env_settings

PROVIDERS = ("mimo", "deepseek")
_FIELDS = ("api_key", "api_url", "model")

# 进程内覆盖缓存：{"ai.deepseek.api_key": "sk-xxx", ...}
_overrides: dict[str, str] = {}


def _valid_key(key: str) -> bool:
    if key == "ai.provider":
        return True
    if not key.startswith("ai."):
        return False
    parts = key.split(".")
    return len(parts) == 3 and parts[1] in PROVIDERS and parts[2] in _FIELDS


async def reload() -> None:
    """从数据库重新加载覆盖值（启动时与每次保存后调用）"""
    from app.core.database import async_session
    from app.models.app_setting import AppSetting

    global _overrides
    async with async_session() as db:
        result = await db.execute(select(AppSetting))
        _overrides = {row.key: (row.value or "") for row in result.scalars() if _valid_key(row.key)}


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
