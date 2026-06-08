# Agent 查询角色和标签指南

当用户询问角色信息或标签时，Agent 应如何处理和响应。

---

## 🎯 查询场景识别

### 用户询问类型

**1. 查询角色信息**：
- "折枝的信息是什么？"
- "查一下娜美的 tag"
- "永夜希尔有 LoRA 吗？"
- "明世有哪些服装？"

**2. 查询标签/类别**：
- "有哪些动作标签？"
- "坐着的 tag 是什么？"
- "2d润彩画风的信息"

**3. 搜索角色**：
- "鸣潮有哪些角色？"
- "搜索所有带银发的角色"
- "原神的角色列表"

---

## 🔧 查询工具

### 1. pretags_manager.py - 主查询工具

**功能**：查询 pretags 数据库中的角色和标签信息

**基本用法**：
```bash
# 搜索角色（模糊匹配）
python modules/pretags-draw/scripts/pretags_manager.py search "折枝"

# 查看角色详细信息
python modules/pretags-draw/scripts/pretags_manager.py info "折枝"

# 列出所有角色
python modules/pretags-draw/scripts/pretags_manager.py list --category character

# 搜索标签
python modules/pretags-draw/scripts/pretags_manager.py search "坐着"

# 统计信息
python modules/pretags-draw/scripts/pretags_manager.py stats
```

**输出格式**：
```json
{
  "cname": "折枝",
  "source": "鸣潮",
  "name": "zhezhi",
  "appearance": "long hair, blue eyes, ...",
  "clothing": "blue dress, white sleeves, ...",
  "has_lora": true,
  "lora_file": "zhezhi-anima",
  "unet_weight": 0.9,
  "clip_weight": 0.9,
  "tags": ["1girl", "long_hair", "blue_dress"]
}
```

### 2. character_query.py - 角色专用查询

**功能**：专门查询角色信息，支持按系列搜索

**基本用法**：
```bash
# 搜索角色
python modules/pretags-draw/scripts/character_query.py "折枝"

# 按系列搜索
python modules/pretags-draw/scripts/character_query.py --series "鸣潮"

# 随机选择一个角色
python modules/pretags-draw/scripts/character_query.py --random "鸣潮"

# 列出所有系列
python modules/pretags-draw/scripts/character_query.py --list-series

# 统计信息
python modules/pretags-draw/scripts/character_query.py --stats
```

---

## 📋 Agent 处理流程

### 场景 1: 查询单个角色信息

**用户**: "折枝的信息是什么？"

**Agent 处理**：
1. 识别查询意图（角色信息查询）
2. 提取角色名："折枝"
3. 调用查询工具：
   ```bash
   python modules/pretags-draw/scripts/pretags_manager.py search "折枝"
   ```
4. 解析返回结果
5. 格式化响应给用户

**响应格式**：
```
折枝（zhezhi）来自鸣潮

基本信息：
- 英文名: zhezhi
- 来源: 鸣潮
- LoRA: ✅ 有（zhezhi-anima，权重 0.9/0.9）

外观特征：
long hair, blue eyes, blue dress, white sleeves, ...

服装：
blue dress, white sleeves, ...

常用标签：
1girl, long_hair, blue_dress, ...
```

### 场景 2: 查询角色是否有 LoRA

**用户**: "娜美有 LoRA 吗？"

**Agent 处理**：
1. 识别查询意图（LoRA 查询）
2. 提取角色名："娜美"
3. 调用查询工具
4. 检查 `has_lora` 字段
5. 响应结果

**响应格式**：
```
娜美（nami）：

✅ 有 LoRA
- 文件名: nami-lol
- UNET 权重: 0.9
- CLIP 权重: 0.9
- 格式: <lora:nami-lol:0.9:0.9>
```

或：
```
娜美（nami）：

❌ 没有 LoRA
- 使用英文名 "nami" 作为提示词
```

### 场景 3: 查询标签/类别信息

**用户**: "坐着的 tag 是什么？"

**Agent 处理**：
1. 识别查询意图（标签查询）
2. 提取关键词："坐着"
3. 调用查询工具：
   ```bash
   python modules/pretags-draw/scripts/pretags_manager.py search "坐着"
   ```
4. 从 `categories.action` 中查找
5. 响应结果

**响应格式**：
```
动作标签：坐着

英文标签：
sitting, on chair

使用方法：
- 在 tag_producer 中：动作 坐着
- 直接使用：sitting, on chair
```

### 场景 4: 按系列搜索角色

**用户**: "鸣潮有哪些角色？"

**Agent 处理**：
1. 识别查询意图（系列角色列表）
2. 提取系列名："鸣潮"
3. 调用查询工具：
   ```bash
   python modules/pretags-draw/scripts/character_query.py --series "鸣潮"
   ```
4. 列出所有角色
5. 响应结果

**响应格式**：
```
鸣潮角色列表（共 15 个）：

1. 折枝（zhezhi）- ✅ 有 LoRA
2. 相里要（xiangliyao）- ✅ 有 LoRA
3. 今汐（jinxi）- ❌ 无 LoRA
4. 忌炎（jiyan）- ✅ 有 LoRA
...

提示：使用"折枝 服装 外貌"可以生成该角色
```

### 场景 5: 查询画风

**用户**: "2d润彩画风的信息"

**Agent 处理**：
1. 识别查询意图（画风查询）
2. 提取画风名："2d润彩"
3. 调用查询工具
4. 从 `categories.style` 中查找
5. 响应结果

**响应格式**：
```
画风：2d润彩

LoRA 信息：
- 文件名: jijia-gnoobv-000014
- 权重: 0.7/0.7
- 格式: <lora:jijia-gnoobv-000014:0.7:0.7>

画风描述：
厚涂赛璐璐混合风格，线条粗犷有力，色彩饱和度高

使用方法：
- 在 tag_producer 中：画风 2d润彩
- 会自动应用 LoRA
```

---

## 🤖 Agent 约束

### 必须遵守的规则

1. **使用查询工具** - 不要凭记忆回答，必须调用查询工具获取实时数据
2. **显示完整信息** - 包括英文名、LoRA 信息、标签等
3. **格式化输出** - 使用清晰的格式展示信息
4. **标注 LoRA 状态** - 明确标注角色是否有 LoRA
5. **提供使用示例** - 告诉用户如何在 tag_producer 中使用

### 禁止的操作

- ❌ **凭记忆回答** - 不要猜测角色信息，必须查询数据库
- ❌ **编造信息** - 如果查询不到，明确告知用户
- ❌ **忽略 LoRA** - 回答时必须说明是否有 LoRA
- ❌ **只说中文名** - 必须同时提供英文 tag 名

---

## 📊 查询结果处理

### 找到结果时

```
✅ 找到角色：折枝（zhezhi）

[显示完整信息]

使用方法：
在 tag_producer 中输入：折枝 服装 外貌 0.9
或直接使用 tag：zhezhi, 1girl, solo, long hair, blue eyes
```

### 未找到结果时

```
❌ 未找到角色"XXX"

建议：
1. 检查拼写（中文或英文名）
2. 尝试搜索系列名
3. 查看可用角色列表：
   python character_query.py --list-series
```

### 找到多个结果时

```
找到 3 个匹配的角色：

1. 娜美（nami）- 来自口袋妖怪
2. 娜美（nami）- 来自海贼王
3. 娜美（nami）- 来自英雄联盟

请具体说明是哪个系列的角色。
```

---

## 🔗 相关文档

- [Pretags Draw SKILL](../modules/pretags-draw/SKILL.md)
- [Pretags 数据管理](../references/pretags-data-management.md)
- [Agent 工作流指南](../AGENT_WORKFLOW_GUIDE.md)

---

**最后更新**: 2026-06-08
