"""部署运维接口（仅管理员）

设计要点：
1. 发布脚本必须以「独立会话」启动 —— 重启后端会杀掉 uvicorn 的子进程，
   所以用 start_new_session=True 让脚本脱离当前进程组继续跑。
2. 接口本身不阻塞：触发后立刻返回，前端轮询 /status 拿进度与日志。
3. 默认关闭（OPS_ENABLED=false），避免误操作把线上服务重启掉。
"""

import json
import os
import platform
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.api.auth import get_current_admin
from app.core.config import settings
from app.models.user import User

router = APIRouter(prefix="/api/admin/ops", tags=["部署运维"])

# 状态里超过这个时间还没更新，视为脚本已异常退出
STALE_SECONDS = 45 * 60


def _detect_project_root() -> Path:
    """定位项目根目录

    线上后端跑在 `.deploy/current` 软链里，直接 resolve 会落到 releases/<版本> 下，
    所以优先按 `.deploy` 切分路径，确保拿到的是仓库根。
    """
    if settings.OPS_PROJECT_DIR.strip():
        return Path(settings.OPS_PROJECT_DIR).expanduser().resolve()

    here = Path(__file__).resolve()
    parts = here.parts
    if ".deploy" in parts:
        return Path(*parts[: parts.index(".deploy")])
    try:
        return here.parents[3]
    except IndexError:
        return Path.cwd()


PROJECT_ROOT = _detect_project_root()
OPS_DIR = PROJECT_ROOT / "ops"
DEPLOY_DIR = PROJECT_ROOT / ".deploy"
STATE_FILE = DEPLOY_DIR / "state.json"
LOG_FILE = DEPLOY_DIR / "ops.log"


def _platform_ok() -> bool:
    return platform.system() != "Windows" and subprocess.run(
        ["bash", "-c", "command -v bash"], capture_output=True
    ).returncode == 0


def _guard() -> None:
    if not settings.OPS_ENABLED:
        raise HTTPException(
            status_code=409,
            detail=(
                "部署运维未开启。在服务器 .env 中设置 OPS_ENABLED=true 后重启后端即可；"
                "未开启时请用命令行：bash ops/deploy.sh"
            ),
        )
    if not _platform_ok():
        raise HTTPException(
            status_code=400,
            detail="当前环境不支持（需 Linux + bash）。本地开发请直接用命令行执行 ops 脚本",
        )
    if not (OPS_DIR / "deploy.sh").exists():
        raise HTTPException(status_code=500, detail=f"未找到发布脚本：{OPS_DIR / 'deploy.sh'}")


def _read_state() -> dict:
    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _is_running(state: dict) -> bool:
    if state.get("status") != "running":
        return False

    pid = state.get("pid")
    if isinstance(pid, int) and pid > 0:
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            # 进程已不在（或权限不足无法探测），说明脚本异常退出但没来得及写状态
            return False

    stamp = str(state.get("updated_at") or "")
    try:
        age = (datetime.now() - datetime.strptime(stamp, "%Y-%m-%d %H:%M:%S")).total_seconds()
        return age < STALE_SECONDS
    except ValueError:
        return False


def _read_revision(release: Path) -> dict:
    info = {}
    rev = release / "REVISION"
    if not rev.exists():
        return info
    try:
        for line in rev.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()
    except OSError:
        pass
    return info


def _current_release_name() -> str:
    link = DEPLOY_DIR / "current"
    try:
        # lexists 能识别悬空软链；resolve 后取版本目录名
        return link.resolve().name if os.path.lexists(link) else ""
    except OSError:
        return ""


# 体积统计要遍历几万个文件，缓存起来避免前端轮询时反复扫盘
_SIZE_CACHE: dict = {}


def _dir_size(path: Path) -> int:
    key = str(path)
    if key in _SIZE_CACHE:
        return _SIZE_CACHE[key]
    total = 0
    try:
        for f in path.rglob("*"):
            if f.is_file() and not f.is_symlink():
                total += f.stat().st_size
    except OSError:
        pass
    _SIZE_CACHE[key] = total
    return total


def _list_releases() -> list:
    root = DEPLOY_DIR / "releases"
    if not root.is_dir():
        return []

    current = _current_release_name()
    items = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name, reverse=True):
        if not entry.is_dir():
            continue
        rev = _read_revision(entry)
        size = _dir_size(entry)
        items.append(
            {
                "name": entry.name,
                "current": entry.name == current,
                "commit": rev.get("commit", entry.name.rsplit("-", 1)[-1]),
                "built_at": rev.get("built_at", ""),
                "subject": rev.get("subject", ""),
                "size_mb": round(size / 1024 / 1024, 1),
            }
        )
    return items


def _tail_log(lines: int = 200) -> list:
    if not LOG_FILE.exists():
        return []
    try:
        with LOG_FILE.open("rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 128 * 1024))
            content = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []
    return content.splitlines()[-lines:]


def _health_ok() -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(settings.OPS_HEALTH_URL, timeout=2) as resp:
            return 200 <= resp.status < 400
    except Exception:
        return False


def _spawn(script: str, extra_args: list) -> None:
    """以独立会话启动脚本（不受后端重启影响）"""
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # systemd 下 PATH 很短，补齐常见目录，避免找不到 npm / python3
    env["PATH"] = env.get("PATH", "") + ":/usr/local/bin:/usr/bin:/bin"
    env["APP_DIR"] = str(PROJECT_ROOT)
    env["SERVICE"] = settings.OPS_SERVICE
    env["HEALTH_URL"] = settings.OPS_HEALTH_URL

    with LOG_FILE.open("a", encoding="utf-8") as out:
        subprocess.Popen(
            ["bash", str(OPS_DIR / script), *extra_args],
            cwd=str(PROJECT_ROOT),
            stdout=out,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )


class DeployRequest(BaseModel):
    ref: Optional[str] = None
    force: bool = False


class RollbackRequest(BaseModel):
    release: Optional[str] = None


@router.get("/status")
async def ops_status(
    lines: int = Query(60, ge=0, le=500),
    current_user: User = Depends(get_current_admin),
):
    """当前版本、操作进度、历史版本与日志尾部"""
    state = _read_state()
    running = _is_running(state)
    if not running and state.get("status") == "running":
        state["status"] = "unknown"
        state.setdefault("error", "上次操作异常中断（未写入结果）")

    return {
        "enabled": settings.OPS_ENABLED,
        "platform_ok": _platform_ok(),
        "service": settings.OPS_SERVICE,
        "health_url": settings.OPS_HEALTH_URL,
        "health_ok": _health_ok(),
        "project_dir": str(PROJECT_ROOT),
        "running": running,
        "state": state,
        "current": _current_release_name(),
        "releases": _list_releases(),
        "log_tail": _tail_log(lines),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.post("/deploy")
async def ops_deploy(
    payload: DeployRequest,
    current_user: User = Depends(get_current_admin),
):
    """一键更新：拉取 → 构建 → 切换 → 重启（失败自动回滚）"""
    _guard()
    if _is_running(_read_state()):
        raise HTTPException(status_code=409, detail="已有发布/回滚正在进行，请等待完成")

    args = []
    if payload.ref:
        args += ["--ref", payload.ref]
    if payload.force:
        args += ["--force"]

    _spawn("deploy.sh", args)
    return {
        "ok": True,
        "message": "已开始发布，页面会在完成后自动刷新状态",
        "action": "deploy",
        "ref": payload.ref or f"{os.getenv('OPS_BRANCH', 'main')}",
    }


@router.post("/rollback")
async def ops_rollback(
    payload: RollbackRequest,
    current_user: User = Depends(get_current_admin),
):
    """一键回滚：切回上一个版本（或指定版本）并重启"""
    _guard()
    if _is_running(_read_state()):
        raise HTTPException(status_code=409, detail="已有发布/回滚正在进行，请等待完成")

    args = []
    if payload.release:
        args += ["--to", payload.release]

    if not payload.release and len(_list_releases()) < 2:
        raise HTTPException(status_code=400, detail="没有可回滚的历史版本")

    _spawn("rollback.sh", args)
    return {"ok": True, "message": "已开始回滚", "action": "rollback", "to": payload.release or "上一个版本"}


@router.get("/log")
async def ops_log(
    lines: int = Query(300, ge=1, le=2000),
    current_user: User = Depends(get_current_admin),
):
    """发布日志（构建失败排查用）"""
    return {"lines": _tail_log(lines), "file": str(LOG_FILE)}
