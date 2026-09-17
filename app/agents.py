"""多智能体协同：主讲老师 / 提问同学 / 笔记助手。"""

from __future__ import annotations

from app.llm import LLMError, chat_once
from app.prompts import DEFAULT_GRADE, get_system_prompt
from app.rag import format_context, retrieve

AGENT_ROLES = {
    "主讲老师": "你是主讲老师，负责清晰、有条理地讲解知识点。输出控制在 200 字以内。",
    "提问同学": (
        "你是班上一个好奇的同学，替学生提出 1-2 个可能的疑惑或追问，"
        "语气自然，不要直接给完整答案。"
    ),
    "笔记助手": (
        "你是笔记助手，把刚才讲解整理成 3-6 条要点或简易思维导图（用缩进文本），"
        "方便复习。"
    ),
}


def run_multi_agents(topic: str, grade: str) -> dict[str, str]:
    """对同一主题依次调用三个角色，返回 {角色: 文本}。"""
    topic = (topic or "").strip()
    if not topic:
        return {
            "主讲老师": "请先输入一个学习主题。",
            "提问同学": "",
            "笔记助手": "",
        }

    grade = grade or DEFAULT_GRADE
    base = get_system_prompt(grade)
    rag_items = []
    try:
        rag_items = retrieve(topic, grade)
    except Exception:  # noqa: BLE001
        rag_items = []
    context = format_context(rag_items)
    context_block = f"\n【知识库参考】\n{context}" if context else ""

    outputs: dict[str, str] = {}
    lecture = ""
    for role, role_prompt in AGENT_ROLES.items():
        try:
            if role == "主讲老师":
                user = f"请讲解主题：{topic}{context_block}"
            elif role == "提问同学":
                user = f"主题：{topic}\n主讲刚说：{lecture[:600]}\n请提出追问。"
            else:
                user = f"主题：{topic}\n主讲内容：{lecture[:800]}\n请整理笔记要点。"

            text = chat_once(
                [
                    {
                        "role": "system",
                        "content": f"{base}\n\n你当前的角色：{role}\n{role_prompt}",
                    },
                    {"role": "user", "content": user},
                ],
                temperature=0.7,
            )
            outputs[role] = text
            if role == "主讲老师":
                lecture = text
        except LLMError as exc:
            outputs[role] = f"（{role}暂不可用：{exc}）"
        except Exception as exc:  # noqa: BLE001
            outputs[role] = f"（{role}出错：{exc}）"

    return outputs
