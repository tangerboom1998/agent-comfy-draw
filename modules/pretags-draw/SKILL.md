---
name: pretags-draw
description: "AI 绘图工作流模块：通过 ComfyUI API 生成图片。内置中文提示词引擎（tag_producer），支持中文关键词自动转换、LoRA 管理、画风预设、批量生成。核心流程：构建提示词 → tag_producer 处理 → Agent 翻译增强 → ComfyUI 生图。"
version: 2.0.0
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

# Pretags Draw

AI 绘图工作流模块，集成中文提示词处理引擎和 ComfyUI API，实现从中文需求到图片生成的完整流程。

## 🚀 快速开始

```bash
# 设置环境变量
export COMFYUI_HOST=http://127.0.0.1:8188

# 生成图片
cd modules/pretags-draw/scripts
python comfyui_draw.py "masterpiece, best quality, 1girl, long hair, smile" \
  --canvas 竖图 --steps 28
```

生成的图片保存在项目根目录的 `output/` 文件夹。

## 🎯 核心功能

- **4 步工作流** - 提示词构建 → tag_producer 处理 → Agent 增强 → 生图
- **中文提示词引擎** - tag_producer 自动转换中文关键词为 SDXL 标签
- **Pretags 数据集成** - 19,000+ 角色和 10,000+ 标签自动查询
- **LoRA 自动管理** - 从 pretags 数据自动提取和应用 LoRA
- **画质自动优化** - 12 项质量检查和自动增强
- **多画布预设** - 竖图、横图、方图等常用尺寸
- **批量生成** - 支持批量角色预览图生成

## ⚙️ 环境配置

**必需环境变量**:
- `COMFYUI_HOST` - ComfyUI 服务地址
  - 示例: `http://127.0.0.1:8188`

**可选环境变量**:
- `COMFYUI_WORKFLOW_PATH` - 自定义工作流文件路径
  - 默认: `./assets/noob_api_fix_upscale_face_detailer.json`
- `COMFYUI_OUTPUT_DIR` - 输出目录
  - 默认: `./output`

**依赖**:
- Python 3.8+
- ComfyUI 服务运行中
- 依赖包: `requests`, `websocket-client`, `pillow`

## 📖 使用示例

### 场景 1: 使用英文提示词直接生图

```bash
python comfyui_draw.py "masterpiece, best quality, 1girl, blue eyes, long hair, smile, dress" \
  --canvas 竖图 --steps 28 --cfg 7.0
```

### 场景 2: 使用 tag_producer 中文指令

```bash
# tag_producer 会自动处理中文指令
python tag_producer.py "折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 撸串 3"
```

**支持的指令格式**:
- 人物: `<角色名> [服装] [外貌] [权重]`
- 类别: `<类别> <标签名> [权重]`（动作、服装、画风、场景等）
- 画师: `撸串 <数量>`

### 场景 3: 从 pretags 数据生成角色图

```python
from pretags_manager import load_pretags, build_character_prompt

# 加载 pretags 数据
pretags = load_pretags()

# 构建角色提示词
character_id = "c23fe569"  # 角色 ID
prompt = build_character_prompt(pretags, character_id)

# 生成图片
import subprocess
subprocess.run([
    "python", "comfyui_draw.py", prompt,
    "--canvas", "竖图", "--steps", "28"
])
```

### 场景 4: 批量生成角色预览图

```bash
# 为所有角色批量生成预览图
python gen_character_previews.py --batch --canvas 方图 --steps 20

# 为指定角色生成预览图
python gen_character_previews.py --character "折枝" --canvas 竖图
```

## 🔧 工作流说明

### 4 步核心流程

```
用户需求
  ↓
[1] 构建初始提示词 - Agent 理解需求并构建结构化提示词
  ↓
[2] tag_producer 处理 - 处理中文指令，查询 pretags，添加 LoRA
  ↓
[3] Agent 翻译增强 - 翻译中文，按层级重组，12 项质量检查
  ↓
[4] ComfyUI 生图 - 调用 API 生成图片
```

### 提示词构建模式

**模式 1: 直接传递**
- 用户提供完整英文提示词
- 直接发送给 ComfyUI

**模式 2: 预构建传递**
- 用户提供简短中文关键词
- 传给 tag_producer 处理
- Agent 在 Step 3 翻译和润色

**模式 3: Agent 构建**
- 用户只说需求（如"生成折枝坐着的图"）
- Agent 按层级结构构建完整提示词

### 质量保证

Agent 在 Step 3 执行 12 项质量检查：

- 零中文字符（除预设指令）
- 画质前缀完整
- 主体、服装、表情、身材、姿势明确
- 镜头角度、场景、光影齐全
- LoRA 权重合理
- 画师标签存在

## 📚 相关文档

- [Pretags Draw 使用规则](../../references/pretags-draw-rules.md) - 详细的使用规则和最佳实践
- [角色预览图生成](../../references/character-preview-generation.md) - 批量预览图生成指南
- [LoRA 格式规范](../../references/lora-format-guide.md) - LoRA 使用规范
- [故障排除](../../references/pretags-draw-troubleshooting.md) - 常见问题解决

## 📄 许可证

MIT License
