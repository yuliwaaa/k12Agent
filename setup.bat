@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal EnableDelayedExpansion

echo ========================================
echo   小智 K12 教学助手 - 一键环境安装
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未检测到 python 命令。
  echo 请先安装 Python 3.10 ~ 3.12，并勾选 "Add python.exe to PATH"。
  echo 下载: https://www.python.org/downloads/
  echo.
  pause
  exit /b 1
)

for /f "tokens=*" %%v in ('python -c "import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")"') do set PYVER=%%v
echo [1/4] 检测到 Python %PYVER%

if not exist ".venv\Scripts\python.exe" (
  echo [2/4] 创建虚拟环境 .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [错误] 创建虚拟环境失败。
    pause
    exit /b 1
  )
) else (
  echo [2/4] 已存在虚拟环境，跳过创建
)

echo [3/4] 安装依赖（首次可能需要几分钟，请保持联网）...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [错误] 依赖安装失败，请检查网络后重试。
  pause
  exit /b 1
)

if not exist ".env" (
  if exist ".env.example" (
    copy /Y ".env.example" ".env" >nul
    echo [4/4] 已生成 .env （从 .env.example 复制）
  ) else (
    echo [4/4] 未找到 .env.example，请手动创建 .env
  )
) else (
  echo [4/4] 已存在 .env，保留不覆盖
)

echo.
echo ========================================
echo   安装完成。请完成最后一步：
echo ========================================
echo   1. 用记事本打开项目里的 .env
echo   2. 填写 DEEPSEEK_API_KEY=你的密钥
echo      获取: https://platform.deepseek.com
echo   3. 保存后，双击 run.bat 启动
echo.
echo   详细说明见: docs\给评委的3步说明.md
echo ========================================
echo.
pause
endlocal
