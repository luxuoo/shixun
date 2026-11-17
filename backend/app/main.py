from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from datetime import datetime
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, tasks, submissions, ai, admin, evaluation, ops
from app.models import (
    User, Class, Task, TaskStep, Submission, AiLog, Score,
    EvalTemplate, EvalPhase, EvalIndicator, EvalScorerConfig, EvalRecord, EvalSnapshot,
    AppSetting
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    # 加载管理后台保存的运行时配置（AI 密钥等，优先于 .env）
    from app.services import app_settings
    try:
        await app_settings.reload()
    except Exception as e:
        print(f"[配置] 运行时配置加载失败（回退 .env）：{e}")
    # 创建上传目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
    # 启动时打印当前 AI 配置，方便排查
    conf = app_settings.provider_config(app_settings.default_provider())
    print(f"[AI] 服务商={conf['label']} 模型={conf['model']} 密钥={'已配置' if conf['api_key'] else '未配置'}")
    if not conf["api_key"]:
        print("[AI] 警告：当前服务商没有 API Key，AI 提示/评分/诊断将不可用")
    # 默认密钥是公开的，任何人都能伪造 JWT，正式部署必须换掉
    if settings.SECRET_KEY in ("your-secret-key-change-in-production", "", "changeme"):
        print("[安全] 警告：SECRET_KEY 仍是默认值，任何拿到源码的人都能伪造登录凭证，请立即修改")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="AI 编程辅助教学系统 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip 压缩：任务列表、看板、AI 报告等 JSON 体积较大，压缩后传输量可降 60%+
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 静态文件服务
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# 注册路由
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(submissions.router)
app.include_router(ai.router)
app.include_router(admin.router)
app.include_router(evaluation.router)
app.include_router(ops.router)


@app.get("/")
async def root():
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": "1.0.0",
        "docs": "/docs"
    }


def _read_revision() -> dict:
    """读取发布脚本写入的 REVISION（线上在 .deploy/releases/<版本>/REVISION）"""
    from pathlib import Path

    for candidate in (
        Path(__file__).resolve().parents[2] / "REVISION",  # backend/app/main.py → 版本根
        Path.cwd().parent / "REVISION",
    ):
        try:
            if candidate.is_file():
                info = {}
                # errors="replace"：发布脚本若按字节截断中文标题，REVISION 可能含
                # 半个汉字（非法 UTF-8）。这里只是读取展示用的元数据，绝不能因此
                # 让进程在导入期崩溃（曾导致 uvicorn 启动即崩、服务反复重启）。
                for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        info[k.strip()] = v.strip()
                return info
        except (OSError, ValueError):
            continue
    return {}


REVISION = _read_revision()
STARTED_AT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.get("/health")
async def health_check():
    """健康检查，同时暴露运行版本

    运维页面据此判断「软链指向的版本」与「进程实际运行的版本」是否一致 ——
    systemd 单元没改到 .deploy/current 时，两者会不一致，页面会直接报警。
    """
    return {
        "status": "healthy",
        "version": app.version,
        "commit": REVISION.get("commit", ""),
        "built_at": REVISION.get("built_at", ""),
        "started_at": STARTED_AT,
        "pid": os.getpid(),
    }
