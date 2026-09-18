"""对话编排：年级 Prompt + RAG + 历史 + DeepSeek。"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.config import MAX_HISTORY_TURNS, MAX_USER_CHARS
from app.llm import LLMError, chat_stream
from app.prompts import DEFAULT_GRADE, get_system_prompt
from app.rag import format_context, retrieve


def _normalize_history(history: list[dict[str, Any]] | None) -> list[dict[str, str]]:
    """兼容 Gradio messages 格式 [{"role","content"}, ...]。"""
    if not history:
        return []
    cleaned: list[dict[str, str]] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant") or content is None:
            continue
        if isinstance(content, list):
            texts = []
            for block in content:
                if isinstance(block, dict) and block.get("text"):
                    texts.append(str(block["text"]))
                elif isinstance(block, str):
                    texts.append(block)
            content = "\n".join(texts)
        text = str(content).strip()
        if text:
            cleaned.append({"role": role, "content": text})
    return cleaned[-(MAX_HISTORY_TURNS * 2) :]


def build_messages(
    user_message: str,
    history: list[dict[str, Any]] | None,
    grade: str,
    rag_items: list[dict] | None = None,
) -> list[dict[str, str]]:
    system = get_system_prompt(grade or DEFAULT_GRADE)
    context = format_context(rag_items or [])
    if context:
        system = (
            f"{system}\n\n"
            "【知识库参考】下面是与学生问题相关的教材片段，请优先依据这些内容回答；"
            "若不足再补充，但不要编造与片段矛盾的事实。\n"
            f"{context}"
        )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    messages.extend(_normalize_history(history))
    messages.append({"role": "user", "content": user_message})
    return messages


def _prepare(
    user_message: str,
    history: list[dict[str, Any]] | None,
    grade: str,
    *,
    use_rag: bool,
) -> tuple[str | None, list[dict], list[dict[str, str]] | None]:
    """返回 (错误文案|None, rag_items, messages|None)。"""
    text = (user_message or "").strip()
    if not text:
        return "请先输入你的问题哦～", [], None
    if len(text) > MAX_USER_CHARS:
        return f"问题太长啦（超过 {MAX_USER_CHARS} 字），请缩短后再问。", [], None

    grade = grade or DEFAULT_GRADE
    rag_items: list[dict] = []
    if use_rag:
        try:
            rag_items = retrieve(text, grade)
        except Exception:  # noqa: BLE001
            rag_items = []
    return None, rag_items, build_messages(text, history, grade, rag_items)


def reply_stream(
    user_message: str,
    history: list[dict[str, Any]] | None,
    grade: str,
    *,
    use_rag: bool = True,
) -> Iterator[tuple[str, list[dict]]]:
    """流式回复：持续 yield (当前已生成文本, RAG结果)。"""
    err, rag_items, messages = _prepare(user_message, history, grade, use_rag=use_rag)
    if err or messages is None:
        yield err or "请先输入你的问题哦～", rag_items
        return

    answer = ""
    try:
        for delta in chat_stream(messages):
            answer += delta
            yield answer, rag_items
        if not answer.strip():
            yield "抱歉，模型返回了空内容，请稍后重试。", rag_items
    except LLMError as exc:
        yield f"抱歉，老师暂时连不上大模型：{exc}", rag_items
    except Exception as exc:  # noqa: BLE001
        yield f"抱歉，回答时出错了：{exc}", rag_items


def reply(
    user_message: str,
    history: list[dict[str, Any]] | None,
    grade: str,
    *,
    use_rag: bool = True,
) -> tuple[str, list[dict]]:
    """非流式封装：取流式最后一帧。"""
    result = ("", [])
    for result in reply_stream(user_message, history, grade, use_rag=use_rag):
        pass
    return result


def format_rag_debug(items: list[dict]) -> str:
    if not items:
        return "（本次未检索到相关知识点）"
    lines = ["检索到的知识片段："]
    for i, item in enumerate(items, 1):
        title = item.get("title") or item.get("source") or f"片段{i}"
        preview = (item.get("content") or "")[:120].replace("\n", " ")
        lines.append(f"{i}. 《{title}》 {preview}…")
    return "\n".join(lines)
