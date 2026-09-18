"""CLI 联调脚本：复用 app.llm 客户端。"""

from __future__ import annotations

import sys
from pathlib import Path

# 保证项目根在 sys.path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DEEPSEEK_API_KEY  # noqa: E402
from app.llm import LLMError, chat_once  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

if not DEEPSEEK_API_KEY:
    print("未检测到环境变量 DEEPSEEK_API_KEY，请先在 .env 中配置后再运行。")
    sys.exit(1)

messages = [{"role": "system", "content": "You are a helpful assistant."}]
print("输入你的问题（exit 退出，clear/reset/新对话 清空历史）：\n")

try:
    while True:
        try:
            user_input = input("input: ").strip()
        except EOFError:
            print("\n对话结束。")
            break

        user_input = user_input.encode("utf-8", errors="replace").decode("utf-8")

        if user_input.lower() in ("exit", "quit", "q"):
            print("对话结束。")
            break

        if user_input.lower() in ("clear", "reset", "新对话"):
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            print("已清空对话历史。\n")
            continue

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        try:
            reply = chat_once(messages)
        except LLMError as exc:
            messages.pop()
            print(f"请求失败: {exc}\n")
            continue

        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}\n")
except KeyboardInterrupt:
    print("\n对话结束。")
