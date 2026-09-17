import os
import sys
from openai import OpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    print("未检测到环境变量 DEEPSEEK_API_KEY，请先设置后再运行。")
    sys.exit(1)

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

messages = [
    {"role": "system", "content": "You are a helpful assistant."}
]

print("输入你的问题（输入 exit 退出）：\n")

try:
    while True:
        try:
            user_input = input("input: ").strip()
        except EOFError:
            print("\n对话结束。")
            break

        # Avoid Windows console surrogate chars breaking the HTTP JSON body.
        user_input = user_input.encode("utf-8", errors="replace").decode("utf-8")

        if user_input.lower() in ("exit", "quit", "q"):
            print("对话结束。")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model="deepseek-flash",
                messages=messages,
                stream=False,
            )
        except Exception as exc:
            messages.pop()
            print(f"请求失败: {exc}\n")
            continue

        reply = (response.choices[0].message.content or "").strip()
        messages.append({"role": "assistant", "content": reply})
        print(f"AI: {reply}\n")
except KeyboardInterrupt:
    print("\n对话结束。")
