#!/bin/bash
# ComfyUI Draw Suite - 项目初始化脚本
# 用于首次克隆后的快速设置

set -e  # 遇到错误立即退出

echo "🎨 ComfyUI Draw Suite - 项目初始化"
echo "================================"
echo ""

# 检查是否在项目根目录
if [ ! -f "README.md" ] || [ ! -f "SKILL.md" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 1. 环境变量配置
echo "📝 步骤 1/5: 检查环境变量配置"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
    echo "⚠️  请编辑 .env 文件配置 COMFYUI_HOST 等必需变量"
else
    echo "✅ .env 文件已存在"
fi
echo ""

# 2. 创建必要目录
echo "📁 步骤 2/5: 创建必要目录"
mkdir -p output
mkdir -p modules/Tanger-Presets-Show/imgs/characters
mkdir -p modules/Tanger-Presets-Show/imgs/tags
echo "✅ 目录结构创建完成"

# 可选：下载角色预览图数据
echo ""
echo "🖼️  检查角色预览图数据"
if [ -f "modules/Tanger-Presets-Show/data/character-data.tar.gz" ]; then
    SIZE=$(du -h modules/Tanger-Presets-Show/data/character-data.tar.gz | cut -f1)
    echo "✅ 角色预览图数据已存在 ($SIZE)"
else
    echo "📦 角色预览图数据 (675MB) 未找到"
    echo "   下载命令："
    echo "   pip install modelscope"
    echo "   modelscope download --dataset tangerboom/character-data character-data.tar.gz --local_dir ./modules/Tanger-Presets-Show/data/"
    echo ""
    read -p "是否安装 modelscope 并下载？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 正在安装 modelscope..."
        pip install modelscope 2>/dev/null || pip3 install modelscope 2>/dev/null

        DATA_DIR="modules/Tanger-Presets-Show/data"
        echo "📦 正在下载角色预览图数据 (675MB)..."
        cd $DATA_DIR
        modelscope download --dataset tangerboom/character-data character-data.tar.gz --local_dir ./
        echo "📦 正在解压..."
        tar xzf character-data.tar.gz
        rm character-data.tar.gz
        cd $PROJECT_ROOT
        echo "✅ 角色预览图数据已就绪 (14,000+ 预览图)"
        echo ""
        echo "   数据来源：https://github.com/hbl917070/DrawingSpells (已获授权使用)"
    else
        echo "⏭️  跳过下载，可后续手动下载"
    fi
fi
echo ""
echo ""

# 3. 检查 Python 版本
echo "🐍 步骤 3/6: 检查 Python 版本"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "✅ Python 版本: $PYTHON_VERSION"

    # 检查版本是否 >= 3.8
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
        echo "✅ Python 版本满足要求 (>= 3.8)"
    else
        echo "⚠️  Python 版本过低，建议使用 3.8 或更高版本"
    fi
else
    echo "❌ 未找到 Python 3，请先安装 Python 3.8+"
    exit 1
fi
echo ""

# 4. 安装依赖
echo "📦 步骤 4/6: 安装 Python 依赖"
read -p "是否安装依赖？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        echo "✅ 依赖安装完成"
    else
        echo "❌ 未找到 requirements.txt"
    fi
else
    echo "⏭️  跳过依赖安装"
fi
echo ""

# 5. 检查 Git LFS
echo "📊 步骤 5/6: 检查 Git LFS（大文件管理）"
if command -v git-lfs &> /dev/null; then
    echo "✅ Git LFS 已安装"

    # 检查 LFS 是否初始化
    if git lfs env &> /dev/null; then
        echo "✅ Git LFS 已初始化"
    else
        echo "⚠️  Git LFS 未初始化，正在初始化..."
        git lfs install
        echo "✅ Git LFS 初始化完成"
    fi

    # 检查数据文件
    if [ -f "pretags/pretags-anima.json" ]; then
        SIZE=$(du -h pretags/pretags-anima.json | cut -f1)
        echo "✅ 数据文件存在: pretags-anima.json ($SIZE)"
    else
        echo "⚠️  数据文件不存在，正在拉取 LFS 文件..."
        git lfs pull
        echo "✅ LFS 文件拉取完成"
    fi
else
    echo "⚠️  Git LFS 未安装"
    echo "   大型数据文件（pretags/*.json）需要 Git LFS 支持"
    echo ""
    echo "   安装方法："
    echo "   - Ubuntu/Debian: sudo apt install git-lfs"
    echo "   - macOS: brew install git-lfs"
    echo "   - Windows: https://git-lfs.github.com/"
    echo ""
    echo "   或者手动下载数据文件到 pretags/ 目录"
fi
echo ""

# 6. 验证配置
echo "🔍 步骤 6/6: 验证配置"
echo "================================"

# 检查 ComfyUI 配置
if [ -f ".env" ]; then
    if grep -q "COMFYUI_HOST=" .env; then
        COMFYUI_HOST=$(grep "COMFYUI_HOST=" .env | cut -d'=' -f2)
        if [ "$COMFYUI_HOST" != "http://127.0.0.1:8188" ]; then
            echo "✅ COMFYUI_HOST 已配置: $COMFYUI_HOST"
        else
            echo "⚠️  COMFYUI_HOST 使用默认值，如需修改请编辑 .env"
        fi
    fi
fi

# 检查数据文件
if [ -f "pretags/pretags-anima.json" ] || [ -f "pretags/pretags-ill-noob.json" ]; then
    echo "✅ Pretags 数据文件已就绪"
else
    echo "❌ 未找到 Pretags 数据文件"
    echo "   请确保 Git LFS 已安装并运行: git lfs pull"
fi

echo ""
echo "✅ 初始化完成！"
echo ""
echo "📚 下一步："
echo "1. 编辑 .env 文件配置 ComfyUI 服务地址"
echo "2. 启动 Tanger-Presets-Show 管理界面："
echo "   cd modules/Tanger-Presets-Show && python3 server.py"
echo "3. 访问 http://localhost:8765"
echo ""
echo "📖 查看完整文档: README.md"
echo "🐛 遇到问题？查看: DATA_MANAGEMENT.md"
