"""
Phoenix AI - Enterprise Configuration Management
Uses pydantic-settings for environment variable validation with .env file support.
"""
import os
from pathlib import Path

# ── Defaults (can be overridden via .env or environment variables) ──
SECRET_KEY = os.environ.get("SECRET_KEY", "phoenix-dev-secret-change-in-production-2024")
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ── CORS ──
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000").split(",")

# ── Database ──
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///ai_project/memory/phoenix.db")

# ── Rate Limits ──
RATE_LIMIT_CHAT = int(os.environ.get("RATE_LIMIT_CHAT", "20"))
RATE_LIMIT_UPLOAD = int(os.environ.get("RATE_LIMIT_UPLOAD", "5"))
RATE_LIMIT_SANDBOX = int(os.environ.get("RATE_LIMIT_SANDBOX", "10"))

# ── Workspace ──
WORKSPACE_DIR = os.environ.get("PHOENIX_WORKSPACE", str(Path.cwd()))

# ── Security ──
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
