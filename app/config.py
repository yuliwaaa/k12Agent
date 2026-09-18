"""统一配置：从项目根目录 .env 加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "") or ""
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL") or "deepseek-flash"

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "") or ""
WANX_MODEL = os.getenv("WANX_MODEL") or "wanx-v1"

SERVER_NAME = os.getenv("SERVER_NAME") or "127.0.0.1"
SERVER_PORT = int(os.getenv("SERVER_PORT") or "7860")
# Gradio 公网临时分享（https://xxxx.gradio.live）
GRADIO_SHARE = (os.getenv("GRADIO_SHARE") or "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

KNOWLEDGE_DIR = ROOT_DIR / "knowledge_base"
CHROMA_DIR = ROOT_DIR / "data" / "chroma"
PROGRESS_DIR = ROOT_DIR / "data" / "progress"
AUDIO_DIR = ROOT_DIR / "data" / "audio"
IMAGE_DIR = ROOT_DIR / "data" / "images"

MAX_HISTORY_TURNS = 12
MAX_USER_CHARS = 2000
RAG_TOP_K = 3


def ensure_data_dirs() -> None:
    for path in (CHROMA_DIR, PROGRESS_DIR, AUDIO_DIR, IMAGE_DIR):
        path.mkdir(parents=True, exist_ok=True)
