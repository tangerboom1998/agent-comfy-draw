# Agent 解析路径说明

当你对 Agent 说"使用 XX 画风、XX 人物生图"时，系统的完整解析和执行路径。

---

## 🎯 核心解析路径

```
用户输入
  ↓
[1] Agent 理解需求（识别画风/人物/动作等）
  ↓
[2] 构建中文指令字符串
  ↓
[3] 调用 tag_producer 处理
  ↓
[4] tag_producer 查询 pretags 数据库
  ↓
[5] 生成英文 prompt + LoRA
  ↓
[6] Agent 翻译优化（如有中文残留）
  ↓
[7] 调用 comfyui_draw.py 生图
  ↓
[8] 返回图片给用户
```

---

## 📝 详细步骤说明

### Step 1: Agent 理解用户需求

**用户输入示例**：
- "用折枝画一张坐着的图"
- "2d润彩画风，永夜希尔，服装和外貌"
- "画个娜美，撸串 4 个画师"

**Agent 解析**：
- 识别角色名：折枝、永夜希尔、娜美
- 识别画风：2d润彩
- 识别动作：坐着
- 识别选项：服装、外貌、撸串

### Step 2: 构建中文指令字符串

Agent 将理解的内容转换为 tag_producer 能识别的格式：

**格式规则**：
```
人物：<角色名> [服装] [外貌] [权重]
类别：<类别> <标签名> [权重]
画师：撸串 <数量>
```

**示例**：
```
"折枝 服装 外貌 0.9"
"动作 坐着"
"画风 2d润彩 0.7"
"撸串 4"
```

**完整指令**：
```
"折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 0.7 撸串 4"
```

### Step 3: 调用 tag_producer

**命令**：
```bash
python modules/pretags-draw/scripts/tag_producer.py "折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 0.7 撸串 4"
```

**tag_producer 执行流程**：
1. 解析指令字符串
2. 识别不同类型的指令（人物/类别/画师）
3. 查询 pretags 数据库

### Step 4: 查询 Pretags 数据库

**数据文件位置**：
- 优先级 1: `$PRETAGS_DATA_PATH` 环境变量
- 优先级 2: `pretags/pretags-anima.json` 或 `pretags-ill-noob.json`
- 优先级 3: `modules/Tanger-Presets-Show/data/pretags.json`

**查询内容**：

**人物查询**（`折枝 服装 外貌 0.9`）：
```json
{
  "characters": {
    "c23fe569": {
      "cname": "折枝",
      "name": "zhezhi",
      "tags": ["1girl", "long_hair", "blue_dress"],
      "appearance": "long hair, blue eyes, ...",
      "clothing": "blue dress, white sleeves, ...",
      "has_lora": true,
      "lora_file": "zhezhi-anima",
      "unet_weight": 0.9,
      "clip_weight": 0.9
    }
  }
}
```

**画风查询**（`画风 2d润彩`）：
```json
{
  "categories": {
    "style": {
      "s8a4f2b1": {
        "name": "2d润彩",
        "lora_file": "jijia-gnoobv-000014",
        "unet_weight": 0.7,
        "clip_weight": 0.7
      }
    }
  }
}
```

**动作查询**（`动作 坐着`）：
```json
{
  "categories": {
    "action": {
      "a9c3d5e2": {
        "name": "坐着",
        "tags": ["sitting", "on chair"]
      }
    }
  }
}
```

### Step 5: 生成英文 Prompt + LoRA

**tag_producer 输出**：

```
masterpiece, best quality, solo,
<lora:zhezhi-anima:0.9:0.9>,
zhezhi, 1girl, long hair, blue eyes, blue dress, white sleeves,
sitting, on chair,
<lora:jijia-gnoobv-000014:0.7:0.7>,
<artist1>, <artist2>, <artist3>, <artist4>
```

**组成部分**：
- 质量前缀：`masterpiece, best quality, solo`
- 角色 LoRA：`<lora:zhezhi-anima:0.9:0.9>`
- 角色标签：`zhezhi, 1girl, long hair...`
- 角色外观：`long hair, blue eyes`
- 角色服装：`blue dress, white sleeves`
- 动作标签：`sitting, on chair`
- 画风 LoRA：`<lora:jijia-gnoobv-000014:0.7:0.7>`
- 画师标签：随机抽取的 4 个画师

### Step 6: Agent 翻译优化（如需要）

如果 prompt 中有中文残留，Agent 会：
1. 翻译中文为英文
2. 按层级重组标签
3. 执行 12 项质量检查
4. 调整权重和顺序

**12 项质量检查**：
- 零中文、画质前缀、主体明确
- 服装/表情/身材/姿势描述
- 镜头/场景/光影
- 权重合理、画师标签

### Step 7: 调用 comfyui_draw.py

**命令**：
```bash
python modules/pretags-draw/scripts/comfyui_draw.py \
  "masterpiece, best quality, solo, <lora:zhezhi-anima:0.9:0.9>, zhezhi, 1girl, long hair, blue eyes, blue dress, sitting, <lora:jijia-gnoobv-000014:0.7:0.7>, <artist1>, <artist2>" \
  --canvas 竖图 --steps 28 --cfg 5.5
```

**执行流程**：
1. 加载工作流 JSON
2. 注入 prompt 到正确节点
3. 提取 LoRA 并设置权重
4. 提交到 ComfyUI API
5. 等待生成完成
6. 下载图片

### Step 8: 返回图片

**输出位置**：
- 默认：`output/CCUI_timestamp.png`
- 自动在对话中显示图片

---

## 🔧 技术实现

### 关键文件

| 文件 | 作用 |
|------|------|
| `modules/pretags-draw/scripts/tag_producer.py` | 中文指令解析引擎 |
| `pretags/pretags-anima.json` | 角色和标签数据库 |
| `modules/pretags-draw/scripts/comfyui_draw.py` | ComfyUI API 调用 |
| `modules/comfyui-api/scripts/comfyui_client.py` | ComfyUI 底层通信 |

### 数据结构

**Pretags 数据库**：
- `characters` - 19,000+ 角色定义
- `categories.action` - 动作标签
- `categories.style` - 画风标签
- `categories.clothing` - 服装标签
- `categories.shot` - 镜头标签
- `categories.scene` - 场景标签

---

## 📋 完整示例

### 用户输入
```
"用折枝，2d润彩画风，画一张坐着的图，撸串4个画师"
```

### Agent 处理
```
1. 解析需求：角色=折枝，画风=2d润彩，动作=坐着，画师=4个
2. 构建指令："折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 0.7 撸串 4"
3. 调用 tag_producer
```

### tag_producer 输出
```
masterpiece, best quality, solo,
<lora:zhezhi-anima:0.9:0.9>,
zhezhi, 1girl, long hair, blue eyes, blue dress, white sleeves,
sitting, on chair,
<lora:jijia-gnoobv-000014:0.7:0.7>,
wlop, ask, fu_mi, sakimichan
```

### ComfyUI 生图
```
→ 调用 ComfyUI API
→ 生成图片
→ 保存到 output/CCUI_20260608_123456.png
→ 返回给用户
```

---

## 🔗 相关文档

- [Pretags Draw SKILL](modules/pretags-draw/SKILL.md)
- [Pretags Draw 使用规则](references/pretags-draw-rules.md)
- [Tag Producer 预设](references/pretags-draw-rules.md#tag-producer-预设)
- [Pretags 数据管理](references/pretags-data-management.md)

---

**最后更新**: 2026-06-08
