from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI编程辅助教学系统"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/teaching.db"
    # 是否打印 SQL 语句（默认关闭，避免日志刷屏与额外开销）
    SQL_ECHO: bool = False

    # ===== AI 配置 =====
    # 当前使用的 AI 服务商：mimo（小米 MiMo）/ deepseek（深度求索）
    AI_PROVIDER: str = "mimo"
    # 单次 AI 请求超时时间（秒）
    AI_TIMEOUT: float = 120.0
    # 失败重试次数（429 / 5xx / 超时会自动重试）
    AI_MAX_RETRIES: int = 2

    # 小米 MiMo API（OpenAI 兼容格式）
    MIMO_API_KEY: str = ""
    MIMO_API_URL: str = "https://token-plan-cn.xiaomimimo.com/v1"
    MIMO_MODEL: str = "mimo-v2.5-pro"

    # DeepSeek API（OpenAI 兼容格式）
    # 可选模型：deepseek-chat（通用对话）/ deepseek-reasoner（深度思考）
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时

    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB

    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def provider_config(self, name: Optional[str] = None) -> dict:
        """获取指定服务商的连接配置

        返回 {name, label, api_key, api_url, model}；未知服务商回退到 mimo。
        """
        key = (name or self.AI_PROVIDER or "mimo").strip().lower()
        if key == "deepseek":
            return {
                "name": "deepseek",
                "label": "DeepSeek",
                "api_key": self.DEEPSEEK_API_KEY,
                "api_url": self.DEEPSEEK_API_URL,
                "model": self.DEEPSEEK_MODEL,
            }
        return {
            "name": "mimo",
            "label": "小米 MiMo",
            "api_key": self.MIMO_API_KEY,
            "api_url": self.MIMO_API_URL,
            "model": self.MIMO_MODEL,
        }

    def available_providers(self) -> list:
        """列出所有服务商及其是否已配置 API Key"""
        return [
            {
                "name": p["name"],
                "label": p["label"],
                "model": p["model"],
                "api_url": p["api_url"],
                "configured": bool(p["api_key"]),
            }
            for p in (self.provider_config("mimo"), self.provider_config("deepseek"))
        ]


settings = Settings()
