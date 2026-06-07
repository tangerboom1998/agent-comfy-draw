# Pretags Draw 使用规则

本文档整理了 pretags-draw 模块的核心使用规则和最佳实践。

---

## 🎯 提示词构建规则

### 角色名识别

当使用中文角色名时，系统会自动查询 pretags 数据库进行识别。

**查询方法**：
```bash
python scripts/pretags_manager.py search <角色名>
```

如果搜索结果包含来源信息（如"鸣潮"、"原神"、"绝区零"），将其识别为角色。

### 必需字段

使用 pretags 数据构建提示词时，必须包含以下字段：

```python
character = pretags_data['characters'][char_id]

# 必需字段
name = character.get('name', '')           # 角色英文名，不可省略
tags = character.get('tags', [])           # 基础标签
appearance = character.get('appearance', '') # 外观描述
clothing = character.get('clothing', '')    # 服装描述
```

**完整示例**：
```python
prompt = f"masterpiece, best quality, {name}, {', '.join(tags)}, {appearance}, {clothing}"
```

### Name 字段规则

`name` 字段必须包含在提示词中，即使角色有 LoRA：

- **有 LoRA** (`has_lora=True`): LoRA 提供身份特征，`name` 提供辅助信息
- **无 LoRA** (`has_lora=False`): `name` 是唯一的角色标识，必须包含

**示例**：
```
娜美 (LOL) 的 name 字段：nami (league of legends)
即使使用了 <lora:nami_lol:0.8>，仍需包含 "nami (league of legends)" 标签
```

---

## 🎨 单角色绘图

### Solo 标签规则

所有单角色绘图必须包含 `solo` 标签，以避免模型生成多个人物或重影。

**使用场景**：
- 1girl 单人立绘
- 1boy 单人角色
- 1other 单一主体

**标准格式**：
```
masterpiece, best quality, solo, <角色名>, 1girl, ...
```

**示例**：
```
masterpiece, best quality, solo, (zhezhi:1.3), 1girl, long hair, blue dress
```

---

## 🔧 Tag Producer 预设指令

tag_producer 是中文提示词处理引擎，支持以下指令格式：

### 人物指令

**格式**：`<角色名> [服装] [外貌] [权重]`

**示例**：
```
永夜希尔 服装 外貌 0.85
```

**功能**：
- 查询 pretags 数据库
- 生成角色标签
- 添加 LoRA（如果有）
- 应用指定权重

### 类别指令

**格式**：`<类别> <标签名> [权重]`

**支持类别**：
- 动作：`动作 睡觉`
- 服装：`服装 和服`
- 镜头：`镜头 特写`
- 画风：`画风 2d润彩 0.7`
- 场景：`场景 海滩`
- 其他：`其他 <标签>`

**示例**：
```
动作 睡觉
画风 2d润彩 0.7
场景 海滩
```

### 画师串指令

**格式**：`撸串 <数量>`

**示例**：
```
撸串 4
```

**功能**：从画师库中随机选取指定数量的画师标签。

### 混合使用

可以组合多种指令：

```
折枝 服装 外貌 0.9
动作 坐着
画风 2d润彩 0.7
撸串 3
```

**注意**：自由中文文本不会被 tag_producer 处理，会原样保留到 Step 3 由 Agent 翻译。

---

## 📐 提示词层级结构

Agent 构建提示词时遵循以下层级顺序：

```
画质 → 画风 → 主体 → 服装 → 表情 → 身材 → 姿势 → 
程度 → 暴露 → 镜头 → 场景 → 光影 → 材质 → 画师
```

**示例**：
```
# 画质
masterpiece, best quality

# 画风
anime style, cel shading

# 主体
1girl, solo, long hair, blue eyes

# 服装
dress, white dress, bare shoulders

# 表情
smile, happy

# 镜头
cowboy shot, from side

# 场景
outdoors, beach, sunset

# 画师
<artist1>, <artist2>
```

---

## ✅ 12 项质量自检

Agent 在 Step 3 会执行以下检查：

1. **零中文**：提示词中无中文字符（除预设指令）
2. **画质前缀**：包含 `masterpiece, best quality`
3. **主体明确**：有 `1girl`/`1boy`/`1other`
4. **服装描述**：包含服装标签
5. **表情描述**：包含表情标签
6. **身材描述**：包含身材特征
7. **姿势描述**：包含姿势或动作
8. **镜头角度**：包含镜头描述
9. **场景设定**：包含场景标签
10. **光影效果**：包含光影描述
11. **权重合理**：LoRA 和强调权重在合理范围
12. **画师标签**：包含画师风格标签

---

## 🔗 相关文档

- [角色预览图生成指南](character-preview-generation.md)
- [LoRA 格式规范](lora-format-guide.md)
- [故障排除](pretags-draw-troubleshooting.md)

---

**最后更新**: 2026-06-07
