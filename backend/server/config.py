"""集中管理环境变量，避免 API Key 和模型名散落在各模块。"""

import os
from pathlib import Path

from dotenv import load_dotenv

from server.paths import (
    BACKEND_ROOT,
    DATA_DIR,
    ENV_FILE,
    PROJECT_ROOT,
    STORAGE_DIR,
    migrate_legacy_data,
)

migrate_legacy_data()
load_dotenv(ENV_FILE)


def _resolve_path(env_key: str, default_relative: str, *, base: Path | None = None) -> str:
    """将 .env 中的相对路径解析为绝对路径。"""
    raw = os.getenv(env_key)
    root = base or BACKEND_ROOT
    if raw:
        p = Path(raw)
        return str(p if p.is_absolute() else root / p)
    if default_relative.startswith("storage/"):
        return str(STORAGE_DIR / Path(default_relative).name)
    return str(root / default_relative)


LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
EMBEDDING_MODEL_NAME = _resolve_path("EMBEDDING_MODEL_NAME", "models/bge-small-zh-v1.5")
LLM_MODEL_URL = os.getenv("LLM_MODEL_URL")
EMBEDDING_MODEL_URL = os.getenv("EMBEDDING_MODEL_URL")
CHROMA_PERSIST_DIR = _resolve_path("CHROMA_PERSIST_DIR", "storage/chroma")
DB_PATH = _resolve_path("DB_PATH", "storage/metadata.db")
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")

JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:8765"
    ).split(",")
    if o.strip()
]

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024

RERANK_ENABLED = os.getenv("RERANK_ENABLED", "true").lower() in ("1", "true", "yes")
RERANK_MODEL_NAME = _resolve_path("RERANK_MODEL_NAME", "models/bge-reranker-base")
RERANK_CANDIDATES = int(os.getenv("RERANK_CANDIDATES", "20"))

SERVE_STATIC = os.getenv("SERVE_STATIC", "").lower() in ("1", "true", "yes")
STATIC_DIR = PROJECT_ROOT / "frontend" / "dist"
APP_PORT = int(os.getenv("PORT", "8765"))


def reload_llm_settings() -> None:
    """Reload LLM-related env vars after settings API update."""
    global LLM_MODEL_NAME, LLM_MODEL_URL, LLM_MODEL_API_KEY
    load_dotenv(ENV_FILE, override=True)
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
    LLM_MODEL_URL = os.getenv("LLM_MODEL_URL")
    LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
