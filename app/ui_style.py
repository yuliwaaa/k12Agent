"""Gradio 视觉主题：字体、配色、图标与排版。"""

from __future__ import annotations

import base64
from pathlib import Path

import gradio as gr

# 品牌色：青绿主色 + 暖橙点缀（避免紫/奶油模板风）
BRAND = {
    "primary": "#0F766E",
    "primary_dark": "#0D5C56",
    "accent": "#EA580C",
    "ink": "#0F172A",
    "muted": "#64748B",
    "surface": "#F8FAFC",
    "card": "#FFFFFF",
    "line": "#E2E8F0",
}

_PUPPY_BG = Path(__file__).resolve().parent.parent / "data" / "images" / "puppy_1080p.png"


def _puppy_data_uri() -> str:
    if not _PUPPY_BG.is_file():
        return ""
    encoded = base64.b64encode(_PUPPY_BG.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _background_css(puppy_uri: str) -> str:
    """全页约 50% 可见：唯一白罩 50%，控件近透明避免叠层冲淡。"""
    if not puppy_uri:
        return """
.gradio-container,
.main,
.wrap {
  background:
    radial-gradient(1200px 480px at 12% -10%, rgba(15, 118, 110, 0.12), transparent 55%),
    radial-gradient(900px 420px at 95% 0%, rgba(234, 88, 12, 0.08), transparent 50%),
    linear-gradient(180deg, #F8FAFC 0%, #EEF2F7 100%) !important;
}
"""
    return f"""
html, body {{
  min-height: 100%;
  background: #E8EDF2 !important;
}}

body::before {{
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: url('{puppy_uri}') center center / cover no-repeat;
  opacity: 1;
}}

body::after {{
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background: rgba(255, 255, 255, 0.5);
}}

.gradio-container {{
  position: relative;
  z-index: 1;
  background: transparent !important;
}}

.gradio-container .main,
.gradio-container .wrap,
.main,
.wrap,
.contain,
.fillable {{
  background: transparent !important;
}}

.block,
.form,
.panel,
.panel-wrap,
.tabitem {{
  background: rgba(255, 255, 255, 0.18) !important;
}}

textarea,
input {{
  background: rgba(255, 255, 255, 0.35) !important;
}}
"""


def build_custom_css() -> str:
    puppy_uri = _puppy_data_uri()
    bg = _background_css(puppy_uri)
    return (
        """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --k12-primary: #0F766E;
  --k12-primary-dark: #0D5C56;
  --k12-accent: #EA580C;
  --k12-ink: #0F172A;
  --k12-muted: #64748B;
  --k12-surface: #F1F5F9;
  --k12-card: #FFFFFF;
  --k12-line: #E2E8F0;
  --k12-radius: 14px;
  --k12-shadow: 0 1px 2px rgba(15, 23, 42, 0.04), 0 8px 24px rgba(15, 118, 110, 0.06);
}

.gradio-container {
  max-width: 1080px !important;
  margin: 0 auto !important;
  font-family: "Plus Jakarta Sans", ui-sans-serif, system-ui, sans-serif !important;
  color: var(--k12-ink) !important;
}

"""
        + bg
        + """
footer { display: none !important; }

.k12-hero {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 1.25rem;
  align-items: center;
  padding: 1.35rem 1.5rem;
  margin: 0.5rem 0 1.25rem;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.22) 0%, rgba(240,253,250,0.28) 100%);
  border: 1px solid rgba(15, 118, 110, 0.18);
  box-shadow: var(--k12-shadow);
}

.k12-logo {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, #0F766E, #0D9488);
  box-shadow: 0 8px 20px rgba(15, 118, 110, 0.28);
  flex-shrink: 0;
}

.k12-logo svg { width: 30px; height: 30px; }

.k12-brand {
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
  color: var(--k12-ink);
  margin: 0;
}

.k12-tagline {
  margin: 0.35rem 0 0;
  font-size: 0.95rem;
  color: var(--k12-muted);
  line-height: 1.5;
  max-width: 42rem;
}

.k12-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.85rem;
}

.k12-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.28rem 0.7rem;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--k12-primary-dark);
  background: rgba(15, 118, 110, 0.12);
  border: 1px solid rgba(15, 118, 110, 0.18);
}

.k12-pill svg {
  width: 14px;
  height: 14px;
  opacity: 0.9;
}

.k12-grade-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.85rem 1.1rem;
  margin-bottom: 0.85rem;
  border-radius: var(--k12-radius);
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid var(--k12-line);
  box-shadow: var(--k12-shadow);
}

.k12-grade-label {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--k12-muted);
}

.k12-grade-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  font-size: 0.88rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--k12-primary), #14B8A6);
}

.k12-grade-badge svg { width: 15px; height: 15px; }

.k12-grade-hint {
  margin: 0;
  font-size: 0.9rem;
  color: var(--k12-muted);
}

.k12-section {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  margin: 0.4rem 0 0.7rem;
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--k12-ink);
}

.k12-section svg {
  width: 20px;
  height: 20px;
  color: var(--k12-primary);
}

.k12-section-desc {
  margin: -0.35rem 0 0.9rem;
  font-size: 0.88rem;
  color: var(--k12-muted);
  line-height: 1.45;
}

.block, .form, .panel-wrap {
  border-radius: var(--k12-radius) !important;
}

label, .label-wrap span {
  font-weight: 600 !important;
  font-size: 0.86rem !important;
  color: var(--k12-ink) !important;
  letter-spacing: 0.01em;
}

button {
  font-family: "Plus Jakarta Sans", sans-serif !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}

button.primary,
.primary {
  background: linear-gradient(135deg, var(--k12-primary), #0D9488) !important;
  border: none !important;
  box-shadow: 0 4px 14px rgba(15, 118, 110, 0.28) !important;
}

button:hover {
  transform: translateY(-1px);
}

.tabs {
  border-radius: 16px !important;
  background: rgba(255,255,255,0.22) !important;
  border: 1px solid var(--k12-line) !important;
  padding: 0.35rem !important;
  box-shadow: var(--k12-shadow) !important;
}

.tab-nav button,
.tabitem {
  font-weight: 600 !important;
}

.tab-nav button.selected {
  color: var(--k12-primary) !important;
  border-bottom-color: var(--k12-primary) !important;
}

.chatbot, textarea, input, .code, .svelte-select-wrap {
  border-radius: 12px !important;
}

.chatbot {
  border: 1px solid var(--k12-line) !important;
  background: rgba(255, 255, 255, 0.28) !important;
}

.k12-toolbar {
  gap: 0.5rem !important;
}

.k12-agent-grid {
  gap: 0.85rem !important;
}

.k12-agent-card {
  padding: 0.15rem;
}

.k12-agent-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 700;
  font-size: 0.92rem;
  margin-bottom: 0.35rem;
  color: var(--k12-ink);
}

.k12-agent-title svg {
  width: 16px;
  height: 16px;
  color: var(--k12-primary);
}

.k12-steps {
  display: grid;
  gap: 0.55rem;
  margin-top: 0.75rem;
}

.k12-step {
  display: grid;
  grid-template-columns: 28px 1fr;
  gap: 0.65rem;
  align-items: start;
  padding: 0.7rem 0.85rem;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid var(--k12-line);
}

.k12-step-num {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  font-size: 0.78rem;
  font-weight: 700;
  color: #fff;
  background: var(--k12-primary);
}

.k12-step p {
  margin: 0;
  font-size: 0.88rem;
  color: var(--k12-muted);
  line-height: 1.45;
}

@media (max-width: 720px) {
  .k12-hero {
    grid-template-columns: 1fr;
    text-align: left;
  }
  .k12-brand { font-size: 1.35rem; }
}
"""
    )


CUSTOM_CSS = build_custom_css()


def build_theme() -> gr.Theme:
    return gr.themes.Soft(
        primary_hue=gr.themes.Color(
            c50="#F0FDFA",
            c100="#CCFBF1",
            c200="#99F6E4",
            c300="#5EEAD4",
            c400="#2DD4BF",
            c500="#14B8A6",
            c600="#0D9488",
            c700="#0F766E",
            c800="#115E59",
            c900="#134E4A",
            c950="#042F2E",
        ),
        secondary_hue="stone",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Plus Jakarta Sans"), "ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=[gr.themes.GoogleFont("JetBrains Mono"), "ui-monospace", "monospace"],
        text_size="md",
        spacing_size="md",
        radius_size="lg",
    ).set(
        button_primary_background_fill="linear-gradient(135deg, #0F766E 0%, #0D9488 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg, #0D5C56 0%, #0F766E 100%)",
        button_primary_text_color="#ffffff",
        block_title_text_weight="600",
        block_label_text_weight="600",
        body_background_fill="transparent",
        block_background_fill="rgba(255, 255, 255, 0.18)",
        border_color_primary="#E2E8F0",
    )


# —— SVG 图标（内联，无外链依赖）——
ICON_MARK = """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M12 3l2.2 4.6L19 8.3l-3.5 3.4.8 4.8L12 14.2 7.7 16.5l.8-4.8L5 8.3l4.8-.7L12 3z" fill="white"/>
</svg>"""

ICON_CHAT = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M21 12a8 8 0 01-9.5 7.9L5 21l1.2-4.2A8 8 0 1121 12z"/>
</svg>"""

ICON_CODE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M8 9l-4 3 4 3M16 9l4 3-4 3M13 6l-2 12"/>
</svg>"""

ICON_QUIZ = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/>
</svg>"""

ICON_AGENTS = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2.5"/><path d="M3 19c0-3 2.5-5 6-5s6 2 6 5"/><path d="M14 19c.3-2 1.8-3.5 4-3.5 1.5 0 2.7.7 3.4 1.7"/>
</svg>"""

ICON_GEAR = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>
</svg>"""

ICON_MIC = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0014 0M12 18v3"/>
</svg>"""

ICON_IMAGE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.5"/><path d="M21 16l-5-5-9 9"/>
</svg>"""

ICON_BOOK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M4 5a2 2 0 012-2h12v16H6a2 2 0 00-2 2V5z"/><path d="M8 7h8M8 11h6"/>
</svg>"""

ICON_TEACHER = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <circle cx="12" cy="8" r="3.5"/><path d="M5 19c1.5-3.5 4-5 7-5s5.5 1.5 7 5"/>
</svg>"""

ICON_NOTE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M7 3h8l4 4v14H7V3z"/><path d="M15 3v5h5M9 12h8M9 16h6"/>
</svg>"""

ICON_GRADE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
  <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>
</svg>"""


def hero_html() -> str:
    return f"""
<div class="k12-hero">
  <div class="k12-logo">{ICON_MARK}</div>
  <div>
    <h1 class="k12-brand">小智 · K12 人工智能通识课助手</h1>
    <p class="k12-tagline">选学段，开始对话式学习。支持知识检索、配图、在线编程、练习批改与多智能体协同讲解。</p>
    <div class="k12-pills">
      <span class="k12-pill">{ICON_CHAT} 对话答疑</span>
      <span class="k12-pill">{ICON_IMAGE} 教学配图</span>
      <span class="k12-pill">{ICON_CODE} 编程沙箱</span>
      <span class="k12-pill">{ICON_QUIZ} 智能练习</span>
      <span class="k12-pill">{ICON_AGENTS} 多智能体</span>
    </div>
  </div>
</div>
""".strip()


def grade_status_html(grade: str, hint: str) -> str:
    return f"""
<div class="k12-grade-bar">
  <div>
    <div class="k12-grade-label">当前学段</div>
    <div style="margin-top:0.35rem">
      <span class="k12-grade-badge">{ICON_GRADE} {grade}</span>
    </div>
  </div>
  <p class="k12-grade-hint">{hint}</p>
</div>
""".strip()


def section_html(icon_svg: str, title: str, desc: str = "") -> str:
    desc_html = f'<p class="k12-section-desc">{desc}</p>' if desc else ""
    return f"""
<div class="k12-section">{icon_svg}<span>{title}</span></div>
{desc_html}
""".strip()


def agent_title_html(icon_svg: str, title: str) -> str:
    return f'<div class="k12-agent-title">{icon_svg}<span>{title}</span></div>'


def demo_steps_html() -> str:
    steps = [
        "选「小学高年级」，问：什么是机器学习？查看知识检索。",
        "点「生成配图」或「朗读回答」，体验多模态。",
        "改选「初中」，同题对比讲解深度。",
        "到「编程」运行模板，再到「练习」「多智能体」。",
    ]
    items = "".join(
        f'<div class="k12-step"><div class="k12-step-num">{i}</div><p>{t}</p></div>'
        for i, t in enumerate(steps, 1)
    )
    return f'<div class="k12-steps">{items}</div>'
