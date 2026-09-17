"""DeepSeek OpenAI 兼容客户端。"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from openai import OpenAI

from app.config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL


class LLMError(RuntimeError):
    """大模型调用失败。"""


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    if not DEEPSEEK_API_KEY:
        raise LLMError("未配置 DEEPSEEK_API_KEY，请在 .env 中填写后重试。")
    return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)


def chat_once(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
) -> str:
    """发送一轮非流式对话，返回助手文本。"""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=model or DEEPSEEK_MODEL,
            messages=messages,
            temperature=temperature,
            stream=False,
        )
    except LLMError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"调用 DeepSeek 失败：{exc}") from exc

    content = (response.choices[0].message.content or "").strip()
    if not content:
        raise LLMError("模型返回了空内容，请稍后重试。")
    return content


def chat_json(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.3,
) -> str:
    """偏结构化输出的对话调用。"""
    return chat_once(messages, model=model, temperature=temperature)
