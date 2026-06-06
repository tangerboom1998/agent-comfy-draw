@echo off
REM ComfyUI Draw Suite - 项目初始化脚本（Windows）
REM 用于首次克隆后的快速设置

echo ========================================
echo 🎨 ComfyUI Draw Suite - 项目初始化
echo ========================================
echo.

REM 1. 环境变量配置
echo 📝 步骤 1/5: 检查环境变量配置
if not exist ".env" (
    copy .env.example .env
    echo ✅ 已创建 .env 文件
    echo ⚠️  请编辑 .env 文件配置 COMFYUI_HOST 等必需变量
) else (
    echo ✅ .env 文件已存在
)
echo.

REM 2. 创建必要目录
echo 📁 步骤 2/5: 创建必要目录
if not exist "output" mkdir output
if not exist "modules\Tanger-Presets-Show\imgs\characters" mkdir modules\Tanger-Presets-Show\imgs\characters
if not exist "modules\Tanger-Presets-Show\imgs\tags" mkdir modules\Tanger-Presets-Show\imgs\tags
echo ✅ 目录结构创建完成
echo.

REM 3. 检查 Python 版本
echo 🐍 步骤 3/5: 检查 Python 版本
python --version 2>nul
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    echo ✅ Python 已安装
)
echo.

REM 4. 安装依赖
echo 📦 步骤 4/5: 安装 Python 依赖
set /p INSTALL_DEPS="是否安装依赖？(y/n): "
if /i "%INSTALL_DEPS%"=="y" (
    if exist "requirements.txt" (
        python -m pip install -r requirements.txt
        echo ✅ 依赖安装完成
    ) else (
        echo ❌ 未找到 requirements.txt
    )
) else (
    echo ⏭️  跳过依赖安装
)
echo.

REM 5. 检查 Git LFS
echo 📊 步骤 5/5: 检查 Git LFS（大文件管理）
git lfs version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git LFS 未安装
    echo    大型数据文件（pretags\*.json）需要 Git LFS 支持
    echo.
    echo    安装方法：
    echo    - 下载安装包: https://git-lfs.github.com/
    echo    - 或使用 Chocolatey: choco install git-lfs
    echo.
    echo    或者手动下载数据文件到 pretags\ 目录
) else (
    echo ✅ Git LFS 已安装

    REM 初始化 Git LFS
    git lfs install

    REM 检查数据文件
    if exist "pretags\pretags-anima.json" (
        echo ✅ 数据文件已存在
    ) else (
        echo ⚠️  数据文件不存在，正在拉取 LFS 文件...
        git lfs pull
        echo ✅ LFS 文件拉取完成
    )
)
echo.

REM 验证配置
echo 🔍 验证配置
echo ========================================

if exist "pretags\pretags-anima.json" (
    echo ✅ Pretags 数据文件已就绪
) else (
    echo ❌ 未找到 Pretags 数据文件
    echo    请确保 Git LFS 已安装并运行: git lfs pull
)

echo.
echo ✅ 初始化完成！
echo.
echo 📚 下一步：
echo 1. 编辑 .env 文件配置 ComfyUI 服务地址
echo 2. 启动 Tanger-Presets-Show 管理界面：
echo    cd modules\Tanger-Presets-Show
echo    python server.py
echo 3. 访问 http://localhost:8765
echo.
echo 📖 查看完整文档: README.md
echo 🐛 遇到问题？查看: DATA_MANAGEMENT.md
echo.

pause
