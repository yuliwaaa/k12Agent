"""通义万相文生图（DashScope）。无 Key 时生成本地示意配图，保证对话框可展示。"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from app.config import DASHSCOPE_API_KEY, IMAGE_DIR, WANX_MODEL, ensure_data_dirs

logger = logging.getLogger(__name__)


def _make_demo_image(prompt: str) -> str:
    """无 API 时的本地示意插图（可在对话框展示）。"""
    from PIL import Image, ImageDraw, ImageFont

    ensure_data_dirs()
    out = IMAGE_DIR / f"demo_{int(time.time())}.png"
    width, height = 768, 512
    img = Image.new("RGB", (width, height), "#0F766E")
    draw = ImageDraw.Draw(img)

    for y in range(height):
        ratio = y / height
        r = int(15 + (20 - 15) * ratio)
        g = int(118 + (180 - 118) * ratio)
        b = int(110 + (200 - 110) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    card = (48, 72, width - 48, height - 72)
    draw.rounded_rectangle(card, radius=28, fill="#F8FAFC")

    title = "K12 教学示意配图"
    subtitle = (prompt or "人工智能课堂").strip()
    if len(subtitle) > 28:
        subtitle = subtitle[:28] + "…"

    try:
        font_title = ImageFont.truetype("msyh.ttc", 36)
        font_body = ImageFont.truetype("msyh.ttc", 22)
        font_tip = ImageFont.truetype("msyh.ttc", 16)
    except OSError:
        font_title = ImageFont.load_default()
        font_body = font_title
        font_tip = font_title

    draw.text((width // 2, 160), title, fill="#0F172A", font=font_title, anchor="mm")
    draw.text((width // 2, 230), subtitle, fill="#0F766E", font=font_body, anchor="mm")
    draw.text(
        (width // 2, 320),
        "未配置 DASHSCOPE_API_KEY 时显示本地示意底图",
        fill="#64748B",
        font=font_tip,
        anchor="mm",
    )
    draw.text(
        (width // 2, 360),
        "配置万相密钥后可生成真实 AI 配图",
        fill="#64748B",
        font=font_tip,
        anchor="mm",
    )

    img.save(out, format="PNG")
    return str(out)


def generate_image(prompt: str) -> tuple[str | None, str]:
    """
    根据提示词生成教学配图。
    返回 (本地图片路径或 None, 状态消息)。
    """
    prompt = (prompt or "").strip()
    if not prompt:
        return None, "请先输入配图描述，或先让 AI 老师回答问题后再点「生成配图」。"

    ensure_data_dirs()

    if not DASHSCOPE_API_KEY:
        try:
            path = _make_demo_image(prompt)
            return path, f"已生成示意配图（未配置万相密钥）：{prompt[:60]}"
        except Exception as exc:  # noqa: BLE001
            logger.exception("demo image failed")
            return None, f"示意配图失败：{exc}"

    try:
        from urllib.request import urlretrieve

        from dashscope import ImageSynthesis
        import dashscope

        dashscope.api_key = DASHSCOPE_API_KEY
        rsp = ImageSynthesis.call(
            model=WANX_MODEL,
            prompt=f"K12人工智能教学插图，清晰易懂，适合课堂展示：{prompt}",
            n=1,
            size="1024*1024",
        )
        if rsp.status_code != 200:
            return None, f"配图失败：{getattr(rsp, 'code', '')} {getattr(rsp, 'message', rsp)}"

        results = getattr(getattr(rsp, "output", None), "results", None) or []
        if not results:
            return None, "配图接口未返回图片。"

        url = results[0].url
        out = IMAGE_DIR / f"wanx_{int(time.time())}.png"
        urlretrieve(url, str(out))
        return str(out), f"配图已生成：{prompt[:60]}"
    except Exception as exc:  # noqa: BLE001
        logger.exception("image generation failed")
        return None, f"配图出错：{exc}"


def suggest_prompt_from_answer(answer: str, topic: str = "") -> str:
    """从回答中提炼简短配图提示词。"""
    topic = (topic or "").strip()
    if topic:
        return topic[:80]
    text = (answer or "").strip().replace("\n", " ")
    return (text[:80] or "人工智能课堂示意图")
