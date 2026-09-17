"""Edge TTS 朗读（偏快：短文本 + 语速 + 缓存）。"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from pathlib import Path

from app.config import AUDIO_DIR, ensure_data_dirs

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"
# 语速略快，缩短播放与合成时间
DEFAULT_RATE = "+20%"
# 只读开头，避免整段长回答拖慢等待
MAX_CHARS = 220
MAX_SENTENCES = 3


def _clean_for_speech(text: str) -> str:
    """去掉 Markdown / 多余空白，适合朗读。"""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"[*_#>\-]+", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[🌟✅❌📚🤖💡⭐]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _clip_for_speed(text: str) -> tuple[str, bool]:
    """截取前几句，返回 (朗读文本, 是否被截断)。"""
    text = _clean_for_speech(text)
    if not text:
        return "", False

    parts = re.split(r"(?<=[。！？!?；;])", text)
    parts = [p.strip() for p in parts if p.strip()]
    clipped = ""
    truncated = False
    for i, part in enumerate(parts):
        if i >= MAX_SENTENCES:
            truncated = True
            break
        candidate = f"{clipped}{part}" if clipped else part
        if len(candidate) > MAX_CHARS and clipped:
            truncated = True
            break
        clipped = candidate
        if len(clipped) >= MAX_CHARS:
            if len(text) > len(clipped):
                truncated = True
            break

    if not clipped:
        clipped = text[:MAX_CHARS]
        truncated = len(text) > MAX_CHARS

    if truncated and not clipped.endswith(("。", "！", "？", "…")):
        clipped = clipped.rstrip("，,、；;：:") + "……"
    return clipped, truncated or len(text) > len(clipped)


def _cache_path(text: str, voice: str, rate: str) -> Path:
    digest = hashlib.md5(f"{voice}|{rate}|{text}".encode("utf-8")).hexdigest()[:16]
    return AUDIO_DIR / f"tts_{digest}.mp3"


def synthesize(
    text: str,
    voice: str = DEFAULT_VOICE,
    *,
    rate: str = DEFAULT_RATE,
) -> tuple[str | None, str]:
    """文字转语音，返回 (音频路径, 状态消息)。"""
    raw = (text or "").strip()
    if not raw:
        return None, "没有可朗读的内容。"

    speak, truncated = _clip_for_speed(raw)
    if not speak:
        return None, "没有可朗读的内容。"

    ensure_data_dirs()
    out = _cache_path(speak, voice, rate)
    if out.exists() and out.stat().st_size > 0:
        tip = "（缓存命中）"
        if truncated:
            tip += f" 仅朗读前 {len(speak)} 字，全文见聊天框。"
        return str(out), f"朗读就绪{tip}"

    # 临时文件写入，成功后再落到缓存名，避免半截文件
    tmp = AUDIO_DIR / f"tts_tmp_{int(time.time() * 1000)}.mp3"

    try:
        import edge_tts

        communicate = edge_tts.Communicate(speak, voice, rate=rate)
        # 同步保存，少一层 asyncio.run 开销
        if hasattr(communicate, "save_sync"):
            communicate.save_sync(str(tmp))
        else:
            import asyncio

            asyncio.run(communicate.save(str(tmp)))

        if not tmp.exists() or tmp.stat().st_size == 0:
            return None, "语音文件生成失败。"

        tmp.replace(out)
        tip = f"已生成（{len(speak)} 字，语速 {rate}）"
        if truncated:
            tip += "。仅朗读开头，完整内容请看聊天框。"
        return str(out), tip
    except Exception as exc:  # noqa: BLE001
        logger.exception("tts failed")
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return None, f"朗读失败：{exc}"
