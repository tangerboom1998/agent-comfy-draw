---
name: comfyui-startup
description: "ComfyUI 本地启动工具：GPU 分配策略、代理配置、端口冲突处理、进程管理。支持单卡/多卡模式，通过环境变量配置路径和参数。"
env:
  required:
    - COMFYUI_PATH: "ComfyUI 安装路径（例如：/path/to/ComfyUI）"
  optional:
    - COMFYUI_PYTHON_PATH: "Python 解释器路径（方式A，推荐。例如：/path/to/anaconda3/envs/comfy311/bin/python）"
    - CONDA_PATH: "Conda 安装路径（方式B。例如：/path/to/anaconda3 或 miniconda3）"
    - COMFYUI_CONDA_ENV: "ComfyUI 的 conda 环境名（方式B。例如：comfy311）"
    - COMFYUI_PORT: "ComfyUI 服务端口（默认：8188）"
    - COMFYUI_HOST: "ComfyUI 服务地址（默认：http://127.0.0.1:8188）"
    - CUDA_VISIBLE_DEVICES: "GPU 配置（例如：0 表示单卡，1,0 表示多卡 GPU 1 优先）"
    - HTTP_PROXY: "HTTP 代理地址（仅下载模型时需要，例如：http://proxy.example.com:2090）"
    - HTTPS_PROXY: "HTTPS 代理地址（仅下载模型时需要，例如：http://proxy.example.com:2090）"
---

# ComfyUI 本地启动

## 环境变量配置

在 `.env` 文件中配置以下变量（参考 `.env.example`）：

```bash
# ComfyUI 安装路径（必需）
COMFYUI_PATH=/path/to/ComfyUI

# Python 环境配置（二选一）
# 方式 A：直接指定 Python 路径（推荐，更简单）
COMFYUI_PYTHON_PATH=/path/to/anaconda3/envs/comfy311/bin/python
#
# 方式 B：通过 Conda 配置（传统方式）
# CONDA_PATH=/path/to/anaconda3        # 或 miniconda3
# COMFYUI_CONDA_ENV=comfy311           # ComfyUI 的 conda 环境名

# 服务配置（可选）
COMFYUI_PORT=8188              # 默认 8188
COMFYUI_HOST=http://127.0.0.1:8188

# 代理配置（可选，仅下载模型时需要）
HTTP_PROXY=http://proxy.example.com:2090
HTTPS_PROXY=http://proxy.example.com:2090

# GPU 配置（可选）
CUDA_VISIBLE_DEVICES=0         # 单卡模式：0 或 1
# CUDA_VISIBLE_DEVICES=1,0     # 多卡模式：GPU 1 优先
```

---

## 启动命令

### 基础启动（推荐）

不使用代理，直接启动（本地推理不需要代理）：

```bash
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen
```

### 单 GPU 模式

```bash
export CUDA_VISIBLE_DEVICES=0
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen
```

### 多 GPU 模式（GPU 1 优先）

```bash
export CUDA_VISIBLE_DEVICES=1,0
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen
```

### 带代理启动（仅下载模型时需要）

```bash
export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export CUDA_VISIBLE_DEVICES=1,0
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen
```

---

## 🎯 GPU 分配策略

每次启动前必须执行 `nvidia-smi` 确认显卡状态：

```
# 执行命令
nvidia-smi

# 查看关键字段
GPU   Name               Memory-Usage
 0    RTX 4090            431MiB / 24564MiB    ← GPU 0 有占用
 1    RTX 4090               0MiB / 24564MiB    ← GPU 1 空闲
```

### 选择逻辑

| 场景 | GPU 配置 | 原因 |
|------|----------|------|
| GPU 0 空闲（<100MiB），GPU 1 空闲 | `CUDA_VISIBLE_DEVICES=0` 或 `1,0` | 均可用，任选 |
| **GPU 0 有占用，GPU 1 空闲** | **`CUDA_VISIBLE_DEVICES=1,0`** ✅ | GPU 1 优先，避免资源争抢 |
| GPU 0 空闲，GPU 1 有占用 | `CUDA_VISIBLE_DEVICES=0` | 只用 GPU 0 |
| GPU 0/1 同时有 0MiB | `CUDA_VISIBLE_DEVICES=0` | 单卡模式，快速启动 |
| 两张卡都满载 (>40GiB 合计已用) | ❌ 不可启动 | 资源不足 |
| 端口已被占用 | ❌ 不可启动 | 先查端口占用原因 |

### 端口冲突检测

```bash
# 检查端口是否已被占用
ss -tlnp | grep ${COMFYUI_PORT:-8188}
# 或
curl -s --connect-timeout 3 http://127.0.0.1:${COMFYUI_PORT:-8188}/system_stats 2>/dev/null

# 如果端口被占用，查看是什么进程
ss -tlnp | grep ${COMFYUI_PORT:-8188} | awk '{print $NF}'
```

如果端口被占用但 nvidia-smi 中对应 GPU 没有活跃进程 → 可能残留僵尸进程，需要 `kill`。

---

## 🚀 启动流程

### ⚠️ Step 0 — 端口确认（必须先做，不能跳过）

**🚨 致命教训（2026-06-01）：公子严厉纠正——"别乱改我的启动端口，按照我原来默认的配置启动"。**
**永远不要硬编码 `--port 8188`。必须先查项目代码里默认配的是什么端口，再用那个端口启动。**

```bash
# 方法1（首选）：从 comfyui_client.py 的默认 host 提取端口
SKILL_DIR=$(pwd)
grep -oP ':\\K\\d+' "$SKILL_DIR/modules/pretags-draw/scripts/comfyui_client.py" | head -1
# → 这个项目里输出 8892（不是 8188！）

# 方法2：从 test_anima.py 提取
grep -oP ':\\K\\d+' "$SKILL_DIR/modules/pretags-draw/scripts/test_anima.py" | head -1
# → 这个项目里输出 8892

# 方法3：检查当前环境变量
echo "COMFYUI_HOST=$COMFYUI_HOST"
echo "COMFYUI_PORT=$COMFYUI_PORT"
```

**端口选择逻辑（严格按此顺序，不可跳过）：**
1. ✅ **第一优先**：comfyui_client.py 中硬编码的默认 host 端口（本项目 = 8892）
2. 第二优先：环境变量 `$COMFYUI_PORT` 或 `$COMFYUI_HOST`
3. **最后回退**：8188（仅当上面全查不到时）

**查完告诉我自己：`PORT=X`（X = 实际查到的值），然后用这个值启动。**

### Step 0a — 必须先杀旧进程再启动

**关键：如果之前有 ComfyUI 进程在跑（即使端口无响应），必须先 kill 再启动，否则新旧进程争抢显存导致 OOM。**

```bash
# 找旧进程（排除 agent 自身）
ps aux | grep "[p]ython.*main.py" | grep -v hermes | grep -v agent
# kill
kill -9 <PID>
```

---

### Step 1 — 检查显卡

```bash
nvidia-smi
```

记录各 GPU 显存使用情况，按选择逻辑决定 GPU 配置。

### Step 2 — 执行启动

使用环境变量配置的路径启动：

```bash
# 基础启动（不使用代理）
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen
```

**关键点**：
- 使用 `conda run` 而不是 `conda activate`（避免非交互式 shell 问题）
- 加 `--no-capture-output` 确保日志能实时看到
- 本地推理不需要代理；代理仅在下载模型时需要

### Step 3 — 验证启动成功

启动后等待约 10-30 秒（模型加载），验证方式：

```bash
# 方式1：API 连通性检查
curl -s --connect-timeout 5 $COMFYUI_HOST/system_stats | python3 -m json.tool

# 预期输出示例（关键字段）：
#   "comfyui_version": "v0.3.x"
#   "system": {
#     "devices": [
#       {"name": "NVIDIA GeForce RTX 4090", "vram_free": 22000+}
#     ]
#   }

# 方式2：确认 GPU 显存被占用
nvidia-smi
# → ComfyUI 进程应占用 1-8GB（取决于已加载的模型）
```

### Step 4 — 更新环境变量（用于生图工具）

如果成功启动，确认 `COMFYUI_HOST` 环境变量指向正确的地址：

```bash
echo $COMFYUI_HOST
# 应输出: http://127.0.0.1:8188（或配置的端口）
```

⚠️ **注意**：生图工具依赖 `COMFYUI_HOST` 环境变量。如果需要覆盖：
```bash
export COMFYUI_HOST=http://127.0.0.1:8188
```

调用本地 ComfyUI API 不需要代理。代理只在需要从 HuggingFace/CivitAI 下载模型时才临时设置。

---

## ⚠️ 常见陷阱

### 陷阱 1：旧进程未清理

**症状**：`nvidia-smi` 显示 GPU 有 python 进程在跑，但端口无响应（超时）
**原因**：之前启动的 ComfyUI 进程残留，模型可能加载一半挂了
**修复**：
```bash
# 找到占用 GPU 的 python 进程（排除 agent 的进程）
ps aux | grep "[p]ython.*main.py" | grep -v hermes | grep -v agent
# kill 旧进程
kill -9 <PID>
# 重新启动
```

### 陷阱 2：端口已被占用

**症状**：ComfyUI 启动后立即报 `[Errno 98] error while attempting to bind on address ('0.0.0.0', PORT): address already in use`
**修复**：
```bash
# 检查并杀掉旧进程
kill $(lsof -ti:${COMFYUI_PORT:-8188}) 2>/dev/null
# 或用 ss 找到 PID
PID=$(ss -tlnp | grep ${COMFYUI_PORT:-8188} | grep -oP 'pid=\K\d+')
kill -9 $PID
# 重新启动
```

### 陷阱 3：GPU 0 已有进程时未切换 GPU

**症状**：GPU 0 已有 python 进程，ComfyUI 与旧进程争抢显存，OOM 或卡顿
**修复**：设置 `CUDA_VISIBLE_DEVICES=1,0` 使用 GPU 1 优先

### 陷阱 4：非交互式 shell 中 conda 未初始化

**症状**：在后台 terminal 中运行启动命令，报 `conda: command not found`
**原因**：非交互式 shell，conda 未通过 profile 初始化，`conda activate` 命令不可用
**修复**：使用 `$CONDA_PATH/bin/conda run -n $CONDA_ENV` 直接运行

**实测验证（2026-05-23）**：
- `conda run` 在 background terminal 中也会报 `command not found`
- 必须用**完整路径**：`$CONDA_EXE run -n comfy311 --no-capture-output python main.py`
- 不要用 `conda run`（不带路径），不要用 `conda activate`（非交互式不支持）

### 陷阱 6：后台大目录删除超时

**症状**：`rm -rf` 一个 1GB+ 目录时，terminal 工具 timeout（BLOCKED: Command timed out）
**原因**：Hermes terminal 有超时限制，单次命令无法删除大量文件
**修复**：分步删除，先删最大的子目录：
```bash
# 先删大目录（如 DrawingSpells 931M, output 543M, assets 233M）
rm -rf big_subdir1/
rm -rf big_subdir2/
# 最后删剩余小文件
rm -rf parent_dir/
```

### 陷阱 5：代理阻断 ComfyUI-Manager（启动挂起）

**症状**：ComfyUI 启动后卡在 "Loading custom nodes" 阶段，日志末尾全是 `Connection timeout to host https://raw.githubusercontent.com/...`
**原因**：设了 `http_proxy`/`https_proxy` 后，ComfyUI-Manager 尝试通过代理访问 GitHub 获取扩展列表，但代理无法连通
**修复**：
```bash
# 方案A：启动时不设代理（推荐 — 本地推理不需要代理）
# 直接 conda run，不 export http_proxy

# 方案B：加 no_proxy 绕过特定域名
export http_proxy=$HTTP_PROXY
export https_proxy=$HTTPS_PROXY
export no_proxy=localhost,127.0.0.1,github.com,raw.githubusercontent.com,huggingface.co
export NO_PROXY=localhost,127.0.0.1,github.com,raw.githubusercontent.com,huggingface.co
```

**经验**：本地推理完全不需要代理。只有需要从 HuggingFace 下载新模型时才临时设代理。

---

## 快速命令速查

```bash
# 基础启动（使用环境变量）
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen

# 多 GPU 模式启动
export CUDA_VISIBLE_DEVICES=1,0
cd $COMFYUI_PATH
$CONDA_PATH/bin/conda run -n $CONDA_ENV --no-capture-output \
  python main.py --port ${COMFYUI_PORT:-8188} --listen

# 检查端口
curl -s --connect-timeout 3 $COMFYUI_HOST/system_stats | python3 -m json.tool

# 查看 GPU 占用
nvidia-smi

# 杀进程
kill $(lsof -ti:${COMFYUI_PORT:-8188})

# 更新 COMFYUI_HOST（如果需要）
export COMFYUI_HOST=http://127.0.0.1:8188
```
