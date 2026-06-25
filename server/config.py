"""集中管理环境变量，避免 API Key 和模型名散落在各模块。"""

import os
from dotenv import load_dotenv

# 从项目根目录的 .env 加载；需在 notes-kb/ 下启动（python -m server.xxx）
load_dotenv()

LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
LLM_MODEL_URL = os.getenv("LLM_MODEL_URL")
EMBEDDING_MODEL_URL = os.getenv("EMBEDDING_MODEL_URL")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR")
DB_PATH = os.getenv("DB_PATH")
LLM_MODEL_API_KEY = os.getenv("LLM_MODEL_API_KEY")
