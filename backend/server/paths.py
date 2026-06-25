"""Project paths: dev monorepo vs desktop app bundle."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def _env_true(name: str) -> bool:
    return os.getenv(name, "").lower() in ("1", "true", "yes")


def is_bundle() -> bool:
    return _env_true("RAGCORE_BUNDLE")


def default_data_dir() -> Path:
    explicit = os.getenv("RAGCORE_DATA_DIR")
    if explicit:
        return Path(explicit).expanduser()
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home()
        return base / "RAGcore"
    return Path.home() / "Library" / "Application Support" / "RAGcore"


def _bundle_resources_dir() -> Path:
    explicit = os.getenv("RAGCORE_BUNDLE_DIR")
    if explicit:
        return Path(explicit).resolve()
    # Mac .app: Contents/MacOS/executable -> Contents/Resources
    exe = Path(sys.argv[0]).resolve()
    contents = exe.parent.parent
    if contents.name == "Contents" and (contents / "Resources").is_dir():
        return contents / "Resources"
    return exe.parent


if is_bundle():
    _RESOURCES = _bundle_resources_dir()
    BACKEND_ROOT = _RESOURCES / "backend"
    PROJECT_ROOT = _RESOURCES
    DATA_DIR = default_data_dir()
else:
    BACKEND_ROOT = Path(__file__).resolve().parent.parent
    PROJECT_ROOT = BACKEND_ROOT.parent
    DATA_DIR = Path(os.getenv("RAGCORE_DATA_DIR", str(BACKEND_ROOT)))

ENV_FILE = DATA_DIR / ".env"
ENV_EXAMPLE = BACKEND_ROOT / ".env.example"
STORAGE_DIR = DATA_DIR / "storage"


def migrate_legacy_data() -> None:
    """Move storage/.env from old zip layout into DATA_DIR (once)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    legacy_storage = BACKEND_ROOT / "storage"
    if legacy_storage.is_dir() and legacy_storage != STORAGE_DIR:
        for name in ("metadata.db", "chroma"):
            src = legacy_storage / name
            dst = STORAGE_DIR / name
            if src.exists() and not dst.exists():
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

    legacy_env = BACKEND_ROOT / ".env"
    if legacy_env.is_file() and not ENV_FILE.is_file():
        shutil.copy2(legacy_env, ENV_FILE)

    if not ENV_FILE.is_file() and ENV_EXAMPLE.is_file():
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)
