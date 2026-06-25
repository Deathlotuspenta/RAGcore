"""Read/write LLM settings in backend/.env."""

import os
from pathlib import Path

from dotenv import dotenv_values, set_key

from server.paths import ENV_FILE, ENV_EXAMPLE

_ENV_PATH = ENV_FILE
_PLACEHOLDER = {"", "your-deepseek-api-key-here"}


def _ensure_env_file() -> Path:
    if not _ENV_PATH.is_file():
        if ENV_EXAMPLE.is_file():
            _ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
            _ENV_PATH.write_text(ENV_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            _ENV_PATH.write_text("", encoding="utf-8")
    return _ENV_PATH


def get_llm_settings() -> dict:
    from server import config

    key = (config.LLM_MODEL_API_KEY or "").strip()
    masked = ""
    if key and key not in _PLACEHOLDER:
        masked = f"{'*' * max(0, len(key) - 4)}{key[-4:]}"

    return {
        "model_name": config.LLM_MODEL_NAME or "deepseek-chat",
        "model_url": config.LLM_MODEL_URL
        or "https://api.deepseek.com/v1/chat/completions",
        "api_key_set": bool(key and key not in _PLACEHOLDER),
        "api_key_masked": masked,
    }


def update_llm_settings(
    *,
    model_name: str | None = None,
    model_url: str | None = None,
    api_key: str | None = None,
) -> dict:
    path = _ensure_env_file()

    if model_name is not None:
        name = model_name.strip()
        if not name:
            raise ValueError("模型名称不能为空")
        set_key(str(path), "LLM_MODEL_NAME", name)
        os.environ["LLM_MODEL_NAME"] = name

    if model_url is not None:
        url = model_url.strip()
        if not url.startswith("http"):
            raise ValueError("模型 API 地址无效")
        set_key(str(path), "LLM_MODEL_URL", url)
        os.environ["LLM_MODEL_URL"] = url

    if api_key is not None:
        key = api_key.strip()
        if len(key) < 10:
            raise ValueError("API Key 格式无效")
        set_key(str(path), "LLM_MODEL_API_KEY", key)
        os.environ["LLM_MODEL_API_KEY"] = key

    from server import config

    config.reload_llm_settings()
    return get_llm_settings()
