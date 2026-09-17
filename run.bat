@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [提示] 尚未安装环境。
  echo 请先双击 setup.bat 完成安装，再运行本文件。
  echo.
  pause
  exit /b 1
)

if not exist ".env" (
  echo [提示] 未找到 .env。
  echo 请先运行 setup.bat，或复制 .env.example 为 .env 并填写 DEEPSEEK_API_KEY。
  echo.
  pause
  exit /b 1
)

echo 正在启动 小智 K12 教学助手...
echo 启动后请在浏览器打开终端中显示的地址（一般为 http://127.0.0.1:7860 ）。
echo 关闭本窗口或按 Ctrl+C 可停止服务。
echo.
".venv\Scripts\python.exe" -m app.main
echo.
pause
