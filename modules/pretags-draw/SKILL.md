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
agent_workflow:
  required_steps:
    - "用户提出生图需求时，必须识别角色名、画风、动作等元素"
    - "构建中文指令字符串传给 tag_producer.py"
    - "调用 tag_producer.py 查询 pretags 数据库"
    - "使用 tag_producer 输出的完整 prompt（含 LoRA）调用 comfyui_draw.py"
  forbidden:
    - "不要跳过 tag_producer，直接构建英文 prompt"
    - "不要手动编写 LoRA 格式，必须从 pretags 获取"
    - "不要忽略用户指定的画风、动作、场景要求"
---

# Pretags Draw

AI 绘图工作流模块，集成中文提示词处理引擎和 ComfyUI API，实现从中文需求到图片生成的完整流程。

## 🤖 Agent 工作流约束

**当用户要求生图时，Agent 必须遵循以下流程**：

### 必须执行的步骤

1. **识别需求元素** - 从用户输入中提取角色名、画风、动作、场景等
2. **构建中文指令** - 按格式组装：`<角色名> 服装 外貌 [权重] 动作 <动作名> 画风 <画风名> [权重] 撸串 <数量>`
3. **调用 tag_producer** - 执行 `python modules/pretags-draw/scripts/tag_producer.py "<中文指令>"`
4. **使用完整输出** - 将 tag_producer 输出的完整 prompt（含 LoRA）传给 comfyui_draw.py

### 根据模型类型调整提示词

**Agent 必须识别使用的模型类型，并相应调整提示词格式**：

#### Anima (Flux) 模型
- ✅ **可以使用短句** - 如 "a girl with long hair standing in moonlight"
- ✅ **画师必须加 @** - `@wlop`, `@big chungus`
- ✅ **添加特殊标签** - `newest, latest, safe`
- ✅ **仅英文** - 不要保留中文
- ✅ **支持语义** - 可以写描述性短句

示例：
```
masterpiece, best quality, newest, latest, safe,
@wlop, @ask,
a girl with long silver hair and red eyes,
wearing a white dress, standing in moonlight,
1girl, solo, castle background
```

#### SDXL (Illustrious/Noob) 模型
- ✅ **使用纯 tag** - 拆分为 Danbooru tag，如 `long_hair, silver_hair, red_eyes`
- ✅ **画师不加 @** - `wlop`, `big_chungus`（用下划线）
- ✅ **保留 LoRA** - 从 pretags 获取的 LoRA 保持原样
- ✅ **仅英文** - 不要保留中文
- ❌ **避免复杂句** - 语义理解弱，tag 效果更好

示例：
```
masterpiece, best quality,
<lora:character_noob:0.9:0.9>,
wlop, big_chungus,
1girl, solo, long_hair, silver_hair, red_eyes,
white_dress, standing, moonlight, castle
```

#### z-image Turbo 模型
- ✅ **自然语言** - 写成完整的句子
- ✅ **支持中文** - 可以保留中文描述
- ✅ **简化质量词** - 不需要冗长的质量标签
- ✅ **强语义理解** - 理解上下文和复杂描述
- ✅ **固定参数** - Steps=4, CFG=1.0

示例：
```
一个银色长发红色眼睛的女孩，
穿着白色连衣裙，
站在月光下，背景是城堡
```

### 模型识别方法

Agent 应通过以下方式识别模型类型：

1. **查看工作流文件名**：
   - `anima-*.json` → Anima (Flux)
   - `*noob*.json` 或 `*ill*.json` → SDXL
   - `z_image*.json` → z-image Turbo

2. **查看 pretags 数据文件**：
   - `pretags-anima.json` → Anima
   - `pretags-ill-noob.json` → SDXL

3. **用户明确指定**：
   - 用户说"用 Anima 画" → Anima
   - 用户说"用 Noob 画" → SDXL

### 禁止的操作

- ❌ **跳过 tag_producer** - 不要直接构建英文 prompt，必须通过 tag_producer 查询 pretags
- ❌ **手动编写 LoRA** - 不要手动写 `<lora:xxx>`，必须从 pretags 数据获取
- ❌ **忽略用户需求** - 不要省略用户指定的画风、动作、场景
- ❌ **猜测角色信息** - 角色不在 pretags 中时，应提示用户而非猜测
- ❌ **忽略模型特性** - 不要对所有模型使用相同格式的提示词
- ❌ **凭记忆回答查询** - 查询角色信息时必须调用查询工具，不要凭记忆

### 角色和标签查询

**当用户查询角色或标签信息时，使用两级查询系统**：

#### 查询流程

1. **Level 1: 查询 Pretags（优先）**：
   ```bash
   python modules/pretags-draw/scripts/pretags_manager.py search "折枝"
   ```
   - 找到 → 返回完整信息（LoRA、权重、外观、服装）
   - 未找到 → 继续 Level 2

2. **Level 2: 查询 Danbooru（备选）**：
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:7890
   python modules/danbooru-tag-scraper/scripts/danbooru.py character "zhezhi"
   ```
   - 找到 → 返回基础信息（英文标签，无 LoRA）
   - 未找到 → 告知用户并提供建议

#### 响应格式

**Pretags 数据**：
```
✅ 找到角色：折枝（zhezhi）
📍 数据来源：Pretags
✅ LoRA：zhezhi-anima (0.9/0.9)
外观：long hair, blue eyes, blue dress...
使用：折枝 服装 外貌 0.9
```

**Danbooru 数据**：
```
⚠️ Pretags 未找到，从 Danbooru 获取
📍 数据来源：Danbooru API
标签：1girl, long_hair, blue_eyes...
❌ 无 LoRA、无中文、无本地化
建议：添加到 Pretags
```

#### 处理规则

- ✅ **严格按优先级** - 先 Pretags，后 Danbooru
- ✅ **标注数据源** - 明确来自哪个数据源
- ✅ **区分完整度** - Pretags 完整，Danbooru 基础
- ✅ **提供建议** - Danbooru 数据建议添加到 Pretags

详见：
- [两级查询方案](../../AGENT_TWO_LEVEL_QUERY.md)
- [Danbooru Tag Scraper](../danbooru-tag-scraper/SKILL.md)

详见：
- [Agent 工作流指南](../../AGENT_WORKFLOW_GUIDE.md)
- [模型提示词对比](../../references/model-prompt-comparison.md)

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
