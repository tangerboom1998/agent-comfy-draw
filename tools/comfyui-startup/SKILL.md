---
name: comfyui-startup
description: "ComfyUI 本地启动管理工具：环境配置、GPU 分配、端口管理、进程控制。支持 Conda 环境和代理配置。"
version: 1.0.0
metadata:
  nanobot:
    emoji: "🚀"
    requires:
      env: ["COMFYUI_PATH"]
---

# ComfyUI Startup

ComfyUI 本地启动管理工具，提供环境配置和进程管理功能。

## 🚀 快速开始

```bash
# 设置环境变量
export COMFYUI_PATH=/path/to/ComfyUI
export CONDA_PATH=/path/to/anaconda3
export CONDA_ENV=comfy311

# 启动 ComfyUI
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port 8188 --listen
```

## 🎯 核心功能

- **环境管理** - Conda/venv 环境自动激活
- **GPU 分配** - 支持单卡/多卡配置
- **端口管理** - 端口冲突检测和自动选择
- **进程控制** - 启动、停止、重启、健康检查
- **代理支持** - HTTP/HTTPS 代理配置

## ⚙️ 环境配置

**必需环境变量**:
- `COMFYUI_PATH` - ComfyUI 安装路径
  - 示例: `/home/user/ComfyUI`

**Python 环境配置（二选一）**:

方式 A - 直接指定 Python 路径（推荐）:
- `COMFYUI_PYTHON_PATH` - Python 可执行文件路径
  - 示例: `/path/to/anaconda3/envs/comfy311/bin/python`

方式 B - 通过 Conda 配置:
- `CONDA_PATH` - Conda 安装路径
- `COMFYUI_CONDA_ENV` - Conda 环境名

**可选环境变量**:
- `COMFYUI_PORT` - 服务端口（默认: 8188）
- `CUDA_VISIBLE_DEVICES` - GPU 配置（默认: 0）
- `HTTP_PROXY` / `HTTPS_PROXY` - 代理配置

## 📖 使用示例

### 场景 1: 单卡模式启动

```bash
export COMFYUI_PATH=/home/user/ComfyUI
export CONDA_PATH=/home/user/anaconda3
export CONDA_ENV=comfy311
export CUDA_VISIBLE_DEVICES=0

cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port 8188 --listen
```

### 场景 2: 多卡模式启动

```bash
# GPU 1 优先，GPU 0 备用
export CUDA_VISIBLE_DEVICES=1,0

cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port 8188 --listen
```

### 场景 3: 使用代理

```bash
export http_proxy=http://proxy.example.com:2090
export https_proxy=http://proxy.example.com:2090

cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port 8188 --listen
```

### 场景 4: 健康检查

```bash
# 检查服务是否运行
curl http://127.0.0.1:8188/system_stats

# 查看进程
ps aux | grep ComfyUI
```

## 🔧 GPU 配置

### CUDA_VISIBLE_DEVICES 说明

控制 ComfyUI 可见的 GPU：

```bash
# 单卡模式 - 仅使用 GPU 0
export CUDA_VISIBLE_DEVICES=0

# 单卡模式 - 仅使用 GPU 1
export CUDA_VISIBLE_DEVICES=1

# 多卡模式 - GPU 1 优先，GPU 0 备用
export CUDA_VISIBLE_DEVICES=1,0

# 禁用 GPU（CPU 模式）
export CUDA_VISIBLE_DEVICES=""
```

### 端口配置

```bash
# 使用默认端口 8188
python main.py --port 8188 --listen

# 使用自定义端口
python main.py --port 8892 --listen
```

## 📚 相关文档

- [ComfyUI API](../../modules/comfyui-api/SKILL.md) - API 使用文档
- [环境配置](../../references/environment-setup.md) - 详细的环境配置说明
- [ComfyUI 常见问题](../../references/comfyui-pitfalls.md) - 故障排除

## 📄 许可证

MIT License
