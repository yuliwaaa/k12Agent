"""AI 出题、批改与本地进度记录。"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from app.config import PROGRESS_DIR, ensure_data_dirs
from app.llm import LLMError, chat_json
from app.prompts import DEFAULT_GRADE, get_system_prompt


def generate_quiz(topic: str, grade: str, context: str = "") -> tuple[list[dict], str]:
    """
    生成 3 道选择题。
    返回 (题目列表, 原始说明/错误信息)。
    每题: {id, question, options: [A..], answer: "A", explanation}
    """
    topic = (topic or "").strip() or "人工智能基础"
    grade = grade or DEFAULT_GRADE
    system = get_system_prompt(grade)
    prompt = f"""请根据学段与主题出 3 道单选题，检测学生是否理解刚学的内容。
主题：{topic}
补充上下文：{context[:800] if context else "无"}

严格输出 JSON 数组，不要 Markdown 代码块，格式示例：
[
  {{
    "question": "问题",
    "options": ["选项A", "选项B", "选项C", "选项D"],
    "answer": "A",
    "explanation": "解析"
  }}
]
answer 只能是 A/B/C/D 之一。
"""
    try:
        raw = chat_json(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
        items = _parse_quiz_json(raw)
        if not items:
            return [], "未能解析出题目，请换个主题再试。"
        for i, item in enumerate(items):
            item["id"] = f"q{i+1}"
        return items[:3], "已生成练习题。"
    except LLMError as exc:
        return [], f"出题失败：{exc}"
    except Exception as exc:  # noqa: BLE001
        return [], f"出题出错：{exc}"


def _parse_quiz_json(raw: str) -> list[dict]:
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fence:
        text = fence.group(1).strip()
    # 截取首个数组
    start, end = text.find("["), text.rfind("]")
    if start >= 0 and end > start:
        text = text[start : end + 1]
    data = json.loads(text)
    if not isinstance(data, list):
        return []
    cleaned: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        q = str(item.get("question", "")).strip()
        options = item.get("options") or []
        if not q or not isinstance(options, list) or len(options) < 2:
            continue
        options = [str(o) for o in options[:4]]
        while len(options) < 4:
            options.append("（无）")
        ans = str(item.get("answer", "A")).strip().upper()[:1]
        if ans not in "ABCD":
            ans = "A"
        cleaned.append(
            {
                "question": q,
                "options": options,
                "answer": ans,
                "explanation": str(item.get("explanation", "")).strip(),
            }
        )
    return cleaned


def grade_answers(quiz: list[dict], answers: dict[str, str]) -> dict[str, Any]:
    """批改。answers: {q1: "A", ...}"""
    details = []
    correct = 0
    for item in quiz:
        qid = item["id"]
        expected = item["answer"]
        got = str(answers.get(qid, "")).strip().upper()[:1]
        ok = got == expected
        if ok:
            correct += 1
        details.append(
            {
                "id": qid,
                "question": item["question"],
                "your_answer": got or "未作答",
                "correct_answer": expected,
                "ok": ok,
                "explanation": item.get("explanation", ""),
            }
        )
    total = len(quiz) or 1
    return {
        "score": correct,
        "total": len(quiz),
        "percent": round(100 * correct / total, 1),
        "details": details,
    }


def format_grade_report(result: dict[str, Any]) -> str:
    lines = [
        f"得分：{result['score']}/{result['total']}（{result['percent']}%）",
        "",
    ]
    for d in result.get("details", []):
        mark = "✅" if d["ok"] else "❌"
        lines.append(f"{mark} {d['id']} 你的答案 {d['your_answer']} / 正解 {d['correct_answer']}")
        lines.append(f"   {d['question']}")
        if d.get("explanation"):
            lines.append(f"   解析：{d['explanation']}")
        lines.append("")
    return "\n".join(lines)


def save_progress(grade: str, topic: str, result: dict[str, Any]) -> str:
    ensure_data_dirs()
    record = {
        "id": str(uuid.uuid4()),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "grade": grade,
        "topic": topic,
        "score": result.get("score"),
        "total": result.get("total"),
        "percent": result.get("percent"),
    }
    path = PROGRESS_DIR / "history.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return str(path)


def load_progress_summary(limit: int = 20) -> str:
    path = PROGRESS_DIR / "history.jsonl"
    if not path.exists():
        return "暂无练习记录。"
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    rows = []
    for line in lines[-limit:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        return "暂无练习记录。"
    out = ["最近练习记录："]
    for r in reversed(rows):
        out.append(
            f"- {r.get('ts')}｜{r.get('grade')}｜{r.get('topic')}｜"
            f"{r.get('score')}/{r.get('total')}（{r.get('percent')}%）"
        )
    return "\n".join(out)
