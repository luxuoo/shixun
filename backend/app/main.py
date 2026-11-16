from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db
from app.api import auth, tasks, submissions, ai, admin, evaluation, ops
from app.models import (
    User, Class, Task, TaskStep, Submission, AiLog, Score,
    EvalTemplate, EvalPhase, EvalIndicator, EvalScorerConfig, EvalRecord, EvalSnapshot
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    await init_db()
    # 创建上传目录
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "images"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "videos"), exist_ok=True)
    # 启动时打印当前 AI 配置，方便排查
    conf = settings.provider_config()
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


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
