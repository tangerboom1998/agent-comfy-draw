---
name: artstyle-test
description: "画风 LoRA 测试评估工具：生成测试图 → Vision 分析画风特征 → 写入 pretags 描述。通过实际生图评估画风效果，确保描述准确可靠。"
version: 1.0.0
metadata:
  nanobot:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
  openclaw:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
---

# Artstyle Test

画风 LoRA 测试评估工具，通过实际生图和 Vision 分析生成准确的画风描述。

## 🚀 快速开始

```bash
# 设置环境变量
export COMFYUI_HOST=http://127.0.0.1:8188

# 测试单个画风（画风名作为位置参数）
cd modules/pretags-draw/scripts
python artstyle_test.py "2d润彩"

# 批量测试前 15 个未描述的画风
cd tools/artstyle-test/scripts
python artstyle_rerun.py --start 0 --limit 15
```

> `artstyle_test.py` 位于 `modules/pretags-draw/scripts/`（生图依赖 pretags-draw）。`artstyle_rerun.py` 位于 `tools/artstyle-test/scripts/`，负责批量调度。

## 🎯 核心功能

- **实测评估** - 通过实际生图评估画风效果，不依赖 Civitai 描述
- **Vision 分析** - 自动分析画风特征（线条、上色、光影、质感）
- **批量处理** - 支持批量测试多个画风 LoRA
- **自动写入** - 测试结果自动写入 pretags.json

## ⚙️ 环境配置

**必需环境变量**:
- `COMFYUI_HOST` - ComfyUI 服务地址
  - 示例: `http://127.0.0.1:8188`

**可选环境变量**:
- `LORA_MODEL_DIR` - LoRA 模型根目录
  - 默认: 从 ComfyUI 配置自动检测
- `PRETAGS_DATA_PATH` - Pretags 数据文件路径
  - 默认: `./pretags/pretags-anima.json`

**依赖**:
- Python 3.8+
- ComfyUI 服务运行中
- pretags-draw 模块

## 📖 使用示例

### 场景 1: 测试单个画风

```bash
cd modules/pretags-draw/scripts
# 直接指定画风名，脚本自动生成测试图并分析
python artstyle_test.py "2d润彩"

# 限制测试数量
python artstyle_test.py --limit 3
```

`artstyle_test.py` 内部用固定 base prompt + 画风 LoRA 生成测试图，再调用 Vision 分析画风特征并写入 pretags.json。

### 场景 2: 批量测试画风

```bash
cd tools/artstyle-test/scripts

# 测试前 15 个未描述的画风
python artstyle_rerun.py --start 0 --limit 15

# 测试指定范围
python artstyle_rerun.py --start 15 --limit 30
```

### 场景 3: 查询待测画风数量

```bash
python -c "
import json, os
pretags_path = os.getenv('PRETAGS_DATA_PATH', './pretags/pretags-anima.json')
with open(pretags_path) as f:
    data = json.load(f)
artstyles = data.get('画风', {})
total = len(artstyles)
empty = sum(1 for v in artstyles.values() if not v.get('画风描述'))
print(f'画风总数: {total}, 待测: {empty}, 已测: {total-empty}')
"
```

## 🔧 工作流程

### 1. 生成测试图

使用固定的 base prompt 配合画风 LoRA 生成测试图：

```bash
# 标准测试配置
--canvas 竖图
--steps 28
--cfg 5.5
LoRA 权重: 0.8:0.8 (unet:clip)
```

**LoRA 格式**: `<lora:filename:0.8:0.8>`

### 2. Vision 分析

自动分析生成图片的画风特征：
- 线条风格（粗细、硬朗/柔和）
- 上色风格（厚涂/赛璐璐/水彩）
- 光影特征（明暗对比、阴影风格）
- 整体质感（CG感/手绘感）

### 3. 生成描述

根据 Vision 分析结果生成简洁的画风描述（30-80字）：

**示例**:
- "厚涂赛璐璐混合风，线条粗犷有力，色彩饱和度高，背景厚涂氛围感强"
- "日系清新平涂，线条纤细柔和，色彩淡雅低饱和，水彩质感"

### 4. 写入 pretags

自动更新 pretags.json 中的画风描述。

## 📚 相关文档

- [画风管理与测试](../../references/artstyle-curation.md) - 画风整理流程和测试规范
- [Pretags Draw](../../modules/pretags-draw/SKILL.md) - 生图工具

## 📄 许可证

MIT License
