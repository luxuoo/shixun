"""部署运维接口（仅管理员）

设计要点：
1. 发布脚本必须以「独立会话」启动 —— 重启后端会杀掉 uvicorn 的子进程，
   所以用 start_new_session=True 让脚本脱离当前进程组继续跑。
2. 接口本身不阻塞：触发后立刻返回，前端轮询 /status 拿进度与日志。
3. 默认关闭（OPS_ENABLED=false），避免误操作把线上服务重启掉。
"""

import asyncio
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


def _health_info() -> dict:
    """请求 /health，拿到进程实际运行的版本（用于发现「服务没换新代码」）"""
    import urllib.request

    try:
        with urllib.request.urlopen(settings.OPS_HEALTH_URL, timeout=2) as resp:
            if not (200 <= resp.status < 400):
                return {}
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}


def _local_identity() -> dict:
    """HTTP 探测失败时的兜底：直接读本进程的版本信息

    这样即使 OPS_HEALTH_URL 配错（比如端口不对），后台仍能显示
    「进程实际在跑哪个提交」，不会因为探测失败就丢掉漂移判断。
    """
    try:
        from app.main import REVISION, STARTED_AT

        return {
            "commit": REVISION.get("commit", ""),
            "built_at": REVISION.get("built_at", ""),
            "started_at": STARTED_AT,
            "pid": os.getpid(),
        }
    except Exception:
        return {}


def _duration(state: dict) -> Optional[int]:
    """按 started_at / finished_at 算耗时（秒）"""
    try:
        start = datetime.strptime(str(state.get("started_at")), "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(str(state.get("finished_at")), "%Y-%m-%d %H:%M:%S")
        return int((end - start).total_seconds())
    except (ValueError, TypeError):
        return state.get("duration_sec") if isinstance(state.get("duration_sec"), int) else None


def _read_history(limit: int = 15) -> list:
    """解析 history.log：时间 | 动作 | 版本 | 提交 | 结果 | 操作者 | 说明"""
    path = DEPLOY_DIR / "history.log"
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError:
        return []

    items = []
    for line in reversed(lines):
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 6:
            continue
        items.append(
            {
                "time": parts[0],
                "action": parts[1],
                "release": parts[2],
                "commit": parts[3],
                "result": parts[4],
                "actor": parts[5],
                "detail": parts[6] if len(parts) > 6 else "",
            }
        )
    return items


def _spawn(script: str, extra_args: list, actor: str = "") -> None:
    """以独立会话启动脚本（不受后端重启影响）

    操作者通过环境变量 OPS_ACTOR 传递，而不是命令行参数 —— 服务器上的
    ops/ 脚本可能比正在运行的后端旧（还没 git pull），旧脚本不认识新参数会直接
    退出（报「未知参数: --actor」）。环境变量对任何版本都无害。
    """
    DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # systemd 下 PATH 很短，补齐常见目录，避免找不到 npm / python3
    env["PATH"] = env.get("PATH", "") + ":/usr/local/bin:/usr/bin:/bin"
    env["APP_DIR"] = str(PROJECT_ROOT)
    env["SERVICE"] = settings.OPS_SERVICE
    env["HEALTH_URL"] = settings.OPS_HEALTH_URL
    if actor:
        env["OPS_ACTOR"] = actor

    with LOG_FILE.open("a", encoding="utf-8") as out:
        subprocess.Popen(
            ["bash", str(OPS_DIR / script), *extra_args],
            cwd=str(PROJECT_ROOT),
            stdout=out,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )


def _git_check() -> dict:
    """拉取远端并比较当前版本，判断有多少新提交（只读，不改任何东西）"""
    root = str(PROJECT_ROOT)

    def run(args, timeout=30):
        return subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    try:
        fetch = run(["fetch", "--quiet", "--tags", "origin"], timeout=30)
        if fetch.returncode != 0:
            return {"ok": False, "error": f"git fetch 失败：{(fetch.stderr or '').strip()[:200]}"}

        current = _current_release_commit()
        if not current:
            latest = run(["rev-parse", "--short=7", "origin/main"])
            return {
                "ok": True,
                "current_commit": "",
                "latest_commit": latest.stdout.strip(),
                "behind": None,
                "commits": [],
                "changed_files": [],
                "note": "还没有发布记录，首次发布会构建全部内容",
            }

        behind = run(["rev-list", "--count", f"{current}..origin/main"])
        log_out = run(["log", "--pretty=%h|%s|%ad|%an", "--date=format:%m-%d %H:%M", "-n", "10", f"{current}..origin/main"])
        diff = run(["diff", "--name-only", f"{current}..origin/main"])

        commits = []
        for line in (log_out.stdout or "").splitlines():
            parts = line.split("|", 3)
            if len(parts) == 4:
                commits.append({"sha": parts[0], "subject": parts[1], "time": parts[2], "author": parts[3]})

        files = [f for f in (diff.stdout or "").splitlines() if f]
        latest = run(["rev-parse", "--short=7", "origin/main"])

        return {
            "ok": True,
            "current_commit": current,
            "latest_commit": latest.stdout.strip(),
            "behind": int((behind.stdout or "0").strip() or 0),
            "commits": commits,
            "changed_files": files[:30],
            "changed_count": len(files),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "git fetch 超时，检查服务器网络或仓库权限"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"{type(e).__name__}: {str(e)[:200]}"}


def _repo_head() -> str:
    """仓库工作区当前检出的提交（面板执行的就是这份脚本）"""
    try:
        out = subprocess.run(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return (out.stdout or "").strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def _current_release_commit() -> str:
    link = DEPLOY_DIR / "current"
    try:
        rev = link / "REVISION"
        if rev.is_file():
            for line in rev.read_text(encoding="utf-8").splitlines():
                if line.startswith("commit="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


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

    releases = _list_releases()
    health = _health_info()
    reachable = bool(health)
    if not health:
        health = _local_identity()
    running_commit = str(health.get("commit") or "")
    current = _current_release_name()
    current_commit = ""
    for item in releases:
        if item["current"]:
            current_commit = item["commit"]
            break

    # 进程跑的版本 ≠ 软链指向的版本 → systemd 单元可能还指着老目录
    drift = bool(running_commit and current_commit and running_commit != current_commit)

    state["duration_sec"] = _duration(state)

    # 面板执行的是仓库工作区的 ops 脚本；工作区没 git pull 就会出现
    # 「线上是新版、按钮跑的是旧脚本」，旧脚本可能不认识新参数或带已修的 bug
    repo_head = _repo_head()
    scripts_stale = bool(repo_head and current_commit and repo_head != current_commit)

    return {
        "enabled": settings.OPS_ENABLED,
        "platform_ok": _platform_ok(),
        "service": settings.OPS_SERVICE,
        "health_url": settings.OPS_HEALTH_URL,
        "health_ok": reachable,
        "running_info": {
            "commit": running_commit,
            "built_at": health.get("built_at", ""),
            "started_at": health.get("started_at", ""),
            "pid": health.get("pid"),
        },
        "drift": drift,
        "project_dir": str(PROJECT_ROOT),
        "running": running,
        "state": state,
        "current": current,
        "current_commit": current_commit,
        "repo_head": repo_head,
        "scripts_stale": scripts_stale,
        "releases": releases,
        "disk_mb": round(sum(r["size_mb"] for r in releases), 1),
        "history": _read_history(15),
        "log_tail": _tail_log(lines),
        "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@router.get("/check")
async def ops_check(current_user: User = Depends(get_current_admin)):
    """检查是否有新提交（只读，可在点更新前先看）"""
    if not _platform_ok():
        raise HTTPException(status_code=400, detail="当前环境不支持（需 Linux + bash）")
    return await asyncio.to_thread(_git_check)


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

    _spawn("deploy.sh", args, actor=current_user.username)
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

    _spawn("rollback.sh", args, actor=current_user.username)
    return {"ok": True, "message": "已开始回滚", "action": "rollback", "to": payload.release or "上一个版本"}


@router.get("/log")
async def ops_log(
    lines: int = Query(300, ge=1, le=2000),
    current_user: User = Depends(get_current_admin),
):
    """发布日志（构建失败排查用）"""
    return {"lines": _tail_log(lines), "file": str(LOG_FILE)}
