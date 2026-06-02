@echo off
REM Tanger-Presets-Show 启动脚本 (Windows)

cd /d "%~dp0"

echo 正在启动 Tanger-Presets-Show 服务器...
echo 访问地址: http://localhost:8765
echo 按 Ctrl+C 停止服务器
echo.

python server.py
pause
