"""K12 教学助手 — Gradio 入口。"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

# 支持直接运行本文件：python app/main.py
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import gradio as gr

from app.agents import run_multi_agents
from app.chat import format_rag_debug, reply_stream
from app.config import GRADIO_SHARE, IMAGE_DIR, SERVER_NAME, SERVER_PORT, ensure_data_dirs
from app.multimodal.image_gen import generate_image, suggest_prompt_from_answer
from app.multimodal.sandbox import TEMPLATES, run_python
from app.multimodal.tts import synthesize
from app.prompts import DEFAULT_GRADE, GRADES
from app.quiz import (
    format_grade_report,
    generate_quiz,
    grade_answers,
    load_progress_summary,
    save_progress,
)
from app.rag import build_index
from app.ui_style import (
    ICON_AGENTS,
    ICON_BOOK,
    ICON_CHAT,
    ICON_CODE,
    ICON_GEAR,
    ICON_IMAGE,
    ICON_MIC,
    ICON_NOTE,
    ICON_QUIZ,
    ICON_TEACHER,
    agent_title_html,
    build_custom_css,
    build_theme,
    demo_steps_html,
    grade_status_html,
    hero_html,
    section_html,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

THEME_HINT = {
    "小学低年级": "卡通暖色 · 故事化讲解，短句比喻为主",
    "小学高年级": "清新活力 · 生活化举例，可类比 Scratch",
    "初中": "沉稳专业 · 可用简单 Python 辅助理解",
    "高中": "学术简洁 · 原理、项目与职业路径",
}


def on_grade_change(grade: str) -> str:
    return grade_status_html(grade, THEME_HINT.get(grade, ""))


def chat_add_user(message: str, history: list[dict[str, Any]] | None):
    """立刻把用户气泡写入对话框并清空输入框。"""
    history = list(history or [])
    text = (message or "").strip()
    if text:
        history.append({"role": "user", "content": text})
    return history, "", text


def chat_bot_stream(
    history: list[dict[str, Any]] | None,
    grade: str,
    last_user: str,
):
    """流式生成助手回复。"""
    history = list(history or [])
    message = (last_user or "").strip()
    if not message:
        yield history, "（请先输入问题）", "", ""
        return

    prior = history[:-1] if history and history[-1].get("role") == "user" else history
    history.append({"role": "assistant", "content": "正在检索并思考…"})
    yield history, "正在检索知识库…", "", message

    for answer, rag_items in reply_stream(message, prior, grade):
        history = history[:-1] + [{"role": "assistant", "content": answer}]
        yield history, format_rag_debug(rag_items), answer, message


def clear_chat():
    return [], "（已清空对话）", "", ""


def on_grade_switch(grade: str):
    """切换学段时清空对话，避免风格串味。"""
    return (
        grade_status_html(grade, THEME_HINT.get(grade, "")),
        [],
        "已切换学段，对话已清空。",
        "",
        "",
    )


def do_tts(last_answer: str):
    path, msg = synthesize(last_answer)
    return path, msg


def do_image(
    prompt: str,
    last_answer: str,
    last_user: str,
    history: list[dict[str, Any]] | None,
):
    """生成配图，并写入对话框（Chatbot）。"""
    text = (prompt or "").strip()
    if not text:
        text = suggest_prompt_from_answer(last_answer, last_user)
    path, msg = generate_image(text)
    history = list(history or [])

    if path:
        # Gradio 6 messages：文本 + 图片组件，在对话框内直接展示
        history.append(
            {
                "role": "assistant",
                "content": [
                    f"为你配了一张教学插图（主题：{text[:40]}）：",
                    gr.Image(value=path),
                ],
            }
        )
    else:
        history.append({"role": "assistant", "content": f"配图未成功：{msg}"})

    return history, path, msg, text


def load_template(name: str) -> str:
    return TEMPLATES.get(name, TEMPLATES["Hello World"])


def do_run_code(code: str) -> str:
    return run_python(code)


def do_gen_quiz(topic: str, grade: str, last_answer: str):
    items, msg = generate_quiz(topic or last_answer[:40], grade, last_answer)
    if not items:
        return (
            msg,
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None),
            [],
            msg,
        )

    def opts(i: int):
        q = items[i]
        labels = [f"{chr(65 + j)}. {o}" for j, o in enumerate(q["options"])]
        return gr.update(
            choices=labels,
            value=None,
            label=f"{q['id']}  {q['question']}",
        )

    summary = "\n\n".join(
        f"{it['id']}. {it['question']}\n"
        + "\n".join(f"  {chr(65 + j)}. {o}" for j, o in enumerate(it["options"]))
        for it in items
    )
    return summary, opts(0), opts(1), opts(2), items, msg


def _choice_to_letter(choice: str | None) -> str:
    if not choice:
        return ""
    return choice.strip()[:1].upper()


def do_grade_quiz(quiz: list, a1: str, a2: str, a3: str, grade: str, topic: str):
    if not quiz:
        return "请先生成题目。", load_progress_summary()
    answers = {
        "q1": _choice_to_letter(a1),
        "q2": _choice_to_letter(a2),
        "q3": _choice_to_letter(a3),
    }
    result = grade_answers(quiz, answers)
    save_progress(grade, topic or "练习", result)
    return format_grade_report(result), load_progress_summary()


def do_agents(topic: str, grade: str, last_user: str):
    t = (topic or last_user or "").strip()
    out = run_multi_agents(t, grade)
    return out.get("主讲老师", ""), out.get("提问同学", ""), out.get("笔记助手", "")


def rebuild_kb():
    stats = build_index(force=True)
    return f"知识库已重建：文件 {stats['files']} 个，切片 {stats['chunks']} 段。"


def build_ui() -> gr.Blocks:
    ensure_data_dirs()
    try:
        stats = build_index(force=False)
        kb_status = f"知识库就绪：{stats.get('chunks', 0)} 段（files={stats.get('files', 0)}）"
    except Exception as exc:  # noqa: BLE001
        kb_status = f"知识库初始化失败：{exc}"

    with gr.Blocks(
        title="小智 · K12 人工智能通识课助手",
        fill_height=False,
    ) as demo:
        gr.HTML(hero_html())

        with gr.Group():
            grade = gr.Radio(
                choices=list(GRADES),
                value=DEFAULT_GRADE,
                label="选择学段",
                elem_classes=["k12-grade-radio"],
            )
            grade_info = gr.HTML(on_grade_change(DEFAULT_GRADE))

        last_answer = gr.State("")
        last_user = gr.State("")
        quiz_state = gr.State([])

        with gr.Tabs():
            with gr.Tab("对话答疑"):
                gr.HTML(
                    section_html(
                        ICON_CHAT,
                        "和小智老师对话",
                        "结合年级风格与知识库检索，回答会显示在下方。可继续朗读或生成配图。",
                    )
                )
                chatbot = gr.Chatbot(
                    label="课堂对话",
                    height=440,
                )
                with gr.Accordion("知识检索详情", open=False):
                    rag_debug = gr.Textbox(
                        label="RAG 检索结果",
                        lines=4,
                        value=kb_status,
                        show_label=True,
                    )
                with gr.Row(elem_classes=["k12-toolbar"]):
                    msg = gr.Textbox(
                        label="输入问题",
                        placeholder="例如：什么是机器学习？",
                        scale=5,
                        lines=1,
                        max_lines=4,
                    )
                    send = gr.Button("发送", variant="primary", scale=1, min_width=96)
                with gr.Row(elem_classes=["k12-toolbar"]):
                    clear_btn = gr.Button("清空对话", scale=1)
                    tts_btn = gr.Button("朗读回答", scale=1)
                    img_btn = gr.Button("生成配图", scale=1, variant="secondary")

                with gr.Row():
                    with gr.Column(scale=1):
                        gr.HTML(section_html(ICON_MIC, "语音朗读", "默认朗读回答开头，便于快速试听。"))
                        tts_audio = gr.Audio(label="朗读音频", type="filepath")
                        tts_status = gr.Textbox(label="语音状态", lines=1)
                    with gr.Column(scale=1):
                        gr.HTML(section_html(ICON_IMAGE, "教学配图", "可留空提示词，将根据最近问答自动提炼。"))
                        img_prompt = gr.Textbox(
                            label="配图提示词",
                            placeholder="可空：自动根据最近问答生成",
                            lines=1,
                        )
                        img_out = gr.Image(label="配图预览", type="filepath", height=220)
                        img_status = gr.Textbox(label="配图状态", lines=1)

                send.click(
                    chat_add_user,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg, last_user],
                ).then(
                    chat_bot_stream,
                    inputs=[chatbot, grade, last_user],
                    outputs=[chatbot, rag_debug, last_answer, last_user],
                )
                msg.submit(
                    chat_add_user,
                    inputs=[msg, chatbot],
                    outputs=[chatbot, msg, last_user],
                ).then(
                    chat_bot_stream,
                    inputs=[chatbot, grade, last_user],
                    outputs=[chatbot, rag_debug, last_answer, last_user],
                )
                clear_btn.click(
                    clear_chat,
                    outputs=[chatbot, rag_debug, last_answer, last_user],
                )
                tts_btn.click(do_tts, inputs=last_answer, outputs=[tts_audio, tts_status])
                img_btn.click(
                    do_image,
                    inputs=[img_prompt, last_answer, last_user, chatbot],
                    outputs=[chatbot, img_out, img_status, img_prompt],
                )

            with gr.Tab("编程沙箱"):
                gr.HTML(
                    section_html(
                        ICON_CODE,
                        "在线 Python 练习",
                        "受限沙箱：禁止系统/网络相关库，最长运行 5 秒。适合课堂动手验证。",
                    )
                )
                with gr.Row():
                    tpl = gr.Dropdown(
                        choices=list(TEMPLATES.keys()),
                        value="Hello World",
                        label="代码模板",
                        scale=3,
                    )
                    run_btn = gr.Button("运行代码", variant="primary", scale=1)
                code = gr.Code(
                    value=TEMPLATES["Hello World"],
                    language="python",
                    label="编辑器",
                )
                code_out = gr.Textbox(label="运行输出", lines=10)
                tpl.change(load_template, inputs=tpl, outputs=code)
                run_btn.click(do_run_code, inputs=code, outputs=code_out)

            with gr.Tab("智能练习"):
                gr.HTML(
                    section_html(
                        ICON_QUIZ,
                        "出题与批改",
                        "根据主题生成 3 道单选题，提交后即时得分与解析，并写入本地学习记录。",
                    )
                )
                with gr.Row():
                    quiz_topic = gr.Textbox(
                        label="练习主题",
                        placeholder="如：机器学习 / 神经网络",
                        scale=4,
                    )
                    gen_btn = gr.Button("AI 出题", variant="primary", scale=1)
                quiz_view = gr.Textbox(label="题目预览", lines=8)
                q1 = gr.Radio(choices=[], label="题目 1")
                q2 = gr.Radio(choices=[], label="题目 2")
                q3 = gr.Radio(choices=[], label="题目 3")
                with gr.Row():
                    grade_btn = gr.Button("提交批改", variant="primary")
                    quiz_msg = gr.Textbox(label="状态", lines=1, scale=2)
                with gr.Row():
                    report = gr.Textbox(label="批改结果", lines=10, scale=1)
                    progress = gr.Textbox(
                        label="学习记录",
                        lines=10,
                        value=load_progress_summary(),
                        scale=1,
                    )
                gen_btn.click(
                    do_gen_quiz,
                    inputs=[quiz_topic, grade, last_answer],
                    outputs=[quiz_view, q1, q2, q3, quiz_state, quiz_msg],
                )
                grade_btn.click(
                    do_grade_quiz,
                    inputs=[quiz_state, q1, q2, q3, grade, quiz_topic],
                    outputs=[report, progress],
                )

            with gr.Tab("多智能体"):
                gr.HTML(
                    section_html(
                        ICON_AGENTS,
                        "协同教学课堂",
                        "主讲讲解 → 提问同学追问 → 笔记助手整理要点，三角色协作完成一轮课。",
                    )
                )
                with gr.Row():
                    agent_topic = gr.Textbox(
                        label="学习主题",
                        placeholder="例如：什么是神经网络",
                        scale=4,
                    )
                    agent_btn = gr.Button("开始协同教学", variant="primary", scale=1)
                with gr.Row(elem_classes=["k12-agent-grid"]):
                    with gr.Column(elem_classes=["k12-agent-card"]):
                        gr.HTML(agent_title_html(ICON_TEACHER, "主讲老师"))
                        teacher = gr.Textbox(label="讲解内容", lines=9, show_label=False)
                    with gr.Column(elem_classes=["k12-agent-card"]):
                        gr.HTML(agent_title_html(ICON_CHAT, "提问同学"))
                        classmate = gr.Textbox(label="追问", lines=9, show_label=False)
                    with gr.Column(elem_classes=["k12-agent-card"]):
                        gr.HTML(agent_title_html(ICON_NOTE, "笔记助手"))
                        notes = gr.Textbox(label="笔记", lines=9, show_label=False)
                agent_btn.click(
                    do_agents,
                    inputs=[agent_topic, grade, last_user],
                    outputs=[teacher, classmate, notes],
                )

            with gr.Tab("系统设置"):
                gr.HTML(
                    section_html(
                        ICON_GEAR,
                        "知识库与演示指引",
                        "维护本地 Markdown 知识索引，并按下面步骤完成 5 分钟演示。",
                    )
                )
                with gr.Row():
                    kb_btn = gr.Button("重建知识库索引", variant="secondary")
                    kb_msg = gr.Textbox(label="知识库状态", value=kb_status, lines=2, scale=3)
                kb_btn.click(rebuild_kb, outputs=kb_msg)
                gr.HTML(section_html(ICON_BOOK, "推荐演示路径"))
                gr.HTML(demo_steps_html())

        grade.change(
            on_grade_switch,
            inputs=grade,
            outputs=[grade_info, chatbot, rag_debug, last_answer, last_user],
        )

    return demo


def main() -> None:
    import socket

    def _pick_port(preferred: int, tries: int = 30) -> int:
        for port in range(preferred, preferred + tries):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((SERVER_NAME, port))
                    return port
                except OSError:
                    continue
        raise OSError(f"在 {preferred}-{preferred + tries - 1} 范围内找不到可用端口。")

    demo = build_ui()
    port = _pick_port(SERVER_PORT)
    if port != SERVER_PORT:
        print(f"端口 {SERVER_PORT} 已被占用，改用 {port}")
    print(f"本机访问: http://127.0.0.1:{port}")
    if GRADIO_SHARE:
        print("正在创建 Gradio 公网分享链接（需联网，请稍候）…")
    demo.queue().launch(
        server_name=SERVER_NAME,
        server_port=port,
        share=GRADIO_SHARE,
        show_error=True,
        theme=build_theme(),
        css=build_custom_css(),
        allowed_paths=[str(IMAGE_DIR)],
    )


if __name__ == "__main__":
    main()
