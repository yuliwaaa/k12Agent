"""受限 Python 代码沙箱（subprocess）。"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SEC = 5
MAX_OUTPUT = 4000

FORBIDDEN = re.compile(
    r"\b(import\s+(os|sys|subprocess|socket|ctypes|multiprocessing|shutil|pathlib)"
    r"|from\s+(os|sys|subprocess|socket|ctypes|multiprocessing|shutil|pathlib)\b"
    r"|__import__|eval\s*\(|exec\s*\(|open\s*\(|compile\s*\()",
    re.IGNORECASE,
)

TEMPLATES: dict[str, str] = {
    "Hello World": 'print("Hello, K12 AI!")\n',
    "循环求和": "total = 0\nfor i in range(1, 6):\n    total += i\n    print(i, total)\n",
    "条件判断": 'score = 85\nif score >= 60:\n    print("及格啦！")\nelse:\n    print("继续加油")\n',
}


def run_python(code: str) -> str:
    code = (code or "").strip()
    if not code:
        return "请先输入 Python 代码。"
    if FORBIDDEN.search(code):
        return "出于安全考虑，禁止使用文件/网络/系统相关能力。请用 print、for、if 等基础语法练习。"

    with tempfile.TemporaryDirectory(prefix="k12_sandbox_") as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(script)],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SEC,
                cwd=tmp,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return f"运行超时（>{TIMEOUT_SEC}s），请检查是否有死循环。"
        except Exception as exc:  # noqa: BLE001
            return f"运行失败：{exc}"

        out = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
        out = out.strip() or "(无输出)"
        if len(out) > MAX_OUTPUT:
            out = out[:MAX_OUTPUT] + "\n…(输出过长已截断)"
        if proc.returncode != 0:
            return f"[退出码 {proc.returncode}]\n{out}"
        return out
