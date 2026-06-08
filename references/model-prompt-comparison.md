# 三种模型的提示词差异对比

Anima (Flux)、SDXL (Illustrious/Noob)、z-image Turbo 三种模型的提示词编写差异说明。

---

## 📊 核心差异对比表

| 特性 | Anima (Flux) | SDXL (Illustrious/Noob) | z-image Turbo |
|------|-------------|------------------------|---------------|
| **架构** | Flux | SDXL | Flux Turbo |
| **语言支持** | ✅ 仅英文 | ✅ 仅英文 | ✅ 中英文都支持 |
| **提示词格式** | tag、短句、**描述段落** | tag、短语 | 短句、长句 |
| **语义理解** | ✅ 语义理解强 | ❌ 弱语义，依赖 tag | ✅ 强语义理解 |
| **画师标签** | `@big chungus` 格式（必须加@） | `big_chungus` 格式 | `@big chungus` 或自然语言 |
| **LoRA 支持** | ❌ 不支持 SDXL LoRA | ✅ 支持 SDXL LoRA | ❌ 不支持 SDXL LoRA |
| **大小写** | 全小写 | 不敏感 | 不敏感 |
| **Steps** | 28-40 | 20-30 | 4-8 (Turbo) |
| **CFG** | 5.5-7.0 | 5.0-7.0 | 1.0 |

---

## 🎯 详细对比

### 1. Anima (Flux 架构)

**模型特点**:
- 基于 Flux 架构，支持语义理解
- 可以使用 tag、短句、**描述性段落**
- 画师必须加 `@` 前缀
- 仅支持英文

**提示词格式**:

**✅ 高级描述段落（最佳效果）**:
```
three fox-eared anime girls with long flowing golden hair and large fluffy fox ears, central adult figure seated gracefully with crossed legs, flanked symmetrically by two younger versions of herself, all fully nude with smooth pale skin and subtle luminous highlights, central figure has amber eyes and a calm direct gaze, left girl leans inward with both hands gently resting on the center figure's chest, right girl stands slightly forward with one index finger lightly touching her lips, green eyes on both companions, long voluminous golden tails cascading behind, pure white background, faint semi-transparent rectangular panel floating behind the figures subtly revealing a close-up of the central character's eyes and hair strands, soft directional diffuse lighting casting gentle rim highlights, clean flowing linework with smooth cel shading, bright and transparent color palette, soft even gradients on skin, calm and healing atmosphere, masterpiece quality, highly detailed
```

**✅ tag + 短句混合**:
```
masterpiece, best quality, newest, latest, safe,
@wlop, @ask,
a girl with long silver hair and red eyes,
wearing a white dress, standing in moonlight,
1girl, solo, night sky, castle background
```

**✅ 纯 tag 也可以**:
```
masterpiece, best quality, newest, latest, safe,
@big chungus,
1girl, solo, long hair, silver hair, red eyes,
white dress, standing, moonlight, night sky
```

**❌ 错误示例**:
```
# 错误1: 画师没加 @
masterpiece, best quality, wlop, 1girl, solo

# 错误2: 使用中文
masterpiece, best quality, @wlop, 一个女孩，长发

# 错误3: SDXL LoRA
<lora:character_sdxl:0.9>, 1girl, solo
```

**关键要求**:
1. **画师格式严格** - 必须 `@artist_name`，如 `@big chungus`, `@wlop`
2. **支持短句** - 可以写 "a girl with long hair" 而不只是 tag
3. **仅英文** - 不支持中文
4. **语义理解** - 理解 "standing in moonlight" 的含义
5. **不支持 LoRA** - 不能使用 `<lora:xxx>` 标签

**推荐参数**:
- Steps: 28-40
- CFG: 5.5-7.0
- Resolution: 1024×1024 或 1024×1536

---

### 2. SDXL (Illustrious/Noob)

**模型特点**:
- 基于 SDXL 架构，训练自 Danbooru
- 严重依赖 tag，语义理解很弱
- 完整支持 SDXL LoRA
- 仅支持英文

**提示词格式**:

**✅ 正确示例（tag 为主）**:
```
masterpiece, best quality,
<lora:character_noob:0.9:0.9>,
<lora:style_noob:0.7:0.7>,
big_chungus,
1girl, solo, long hair, silver hair, red eyes,
white dress, standing, night, moonlight,
castle, outdoors
```

**✅ 带短语也可以（但不如纯 tag）**:
```
masterpiece, best quality,
1girl, solo, long silver hair, red eyes,
white dress, standing at night
```

**❌ 错误示例**:
```
# 错误1: 使用复杂句子（语义理解弱）
a beautiful girl with flowing silver hair standing gracefully under the moonlight

# 错误2: 使用中文
1girl, 独自, 长发, 银发

# 错误3: 画师加了 @（Noob 不需要）
@wlop, 1girl, solo
```

**关键要求**:
1. **tag 为主** - 最好使用 Danbooru tag，如 `long_hair`, `red_eyes`
2. **画师不加 @** - 直接写 `wlop`, `big_chungus`
3. **仅英文** - 不支持中文
4. **弱语义** - 复杂句子效果差，拆成 tag 更好
5. **LoRA 支持** - 支持 `<lora:filename:unet:text>` 格式

**LoRA 格式规范**:
```
<lora:filename:unet_weight:text_weight(optional)>
        ↑      ↑          ↑
        |      |          └─ Text 权重（可选，默认=UNET权重）
        |      └──────────── UNET 权重
        └─────────────────── 文件名（不含 .safetensors 后缀和目录路径）

示例：
<lora:jijia-anima-Tanger:0.8>           # 仅 UNET 权重
<lora:jijia-anima-Tanger:0.8:0.8>       # UNET + Text 权重
<lora:zhezhi-anima:0.9:0.9>
<lora:nami-lol:0.8>
```

**规则**:
- 文件名不带 `.safetensors` 扩展名
- 文件名不带目录路径（如 `画风/...`）
- SDXL 通常用双权重 `<lora:xxx:0.8:0.8>`（unet:clip）
- Flux/Anima 不支持 SDXL LoRA
- 必须使用 `<lora:...>` 括号包裹

**推荐参数**:
- Steps: 20-30
- CFG: 5.0-7.0
- Resolution: 1024×1024 或 832×1216

---

### 3. z-image Turbo

**模型特点**:
- 基于 Flux Turbo 架构
- 强大的自然语言理解
- 支持中英文
- 4 步快速生图

**提示词格式**:

**✅ 正确示例（自然语言）**:
```
一个长着银色长发和红色眼睛的女孩，
穿着白色连衣裙，站在月光下，
背景是夜晚的城堡
```

**✅ 英文长句**:
```
A beautiful girl with long flowing silver hair and captivating red eyes,
wearing an elegant white dress,
standing gracefully under the soft moonlight,
with a majestic castle in the background under the starry night sky
```

**✅ 中英文混合**:
```
a girl with silver hair, 穿着白色裙子,
standing under moonlight, 背景是城堡
```

**✅ 简化 tag 也可以**:
```
1girl, solo, silver hair, long hair, red eyes,
white dress, moonlight, castle, night
```

**关键要求**:
1. **自然语言优先** - 可以写完整的句子
2. **中英文都支持** - 可以用中文描述
3. **强语义理解** - 理解上下文和复杂描述
4. **简化为主** - 不需要冗长的质量标签
5. **快速生成** - 4 步即可出图

**推荐参数**:
- Steps: 4（固定，Turbo 特性）
- CFG: 1.0（固定）
- Resolution: 1280×1280

---

## 🔄 实际使用对比

### 同一需求的不同写法

**需求**: 画一个银发红瞳的女孩穿白裙站在月光下

#### Anima (Flux) - tag + 短句混合
```
masterpiece, best quality, newest, latest, safe,
@wlop,
a girl with long silver hair and red eyes,
wearing a white dress, standing in moonlight,
1girl, solo, night sky, castle background
```

#### SDXL (Illustrious/Noob) - 纯 tag
```
masterpiece, best quality,
<lora:style_noob:0.7:0.7>,
wlop,
1girl, solo, long_hair, silver_hair, red_eyes,
white_dress, standing, moonlight, night,
castle, outdoors
```

#### z-image Turbo - 自然语言
```
一个银色长发红色眼睛的女孩，
穿着白色连衣裙，
站在月光下，背景是城堡
```

或英文长句：
```
A girl with long silver hair and red eyes,
wearing a white dress,
standing under the moonlight with a castle in the background
```

---

## 📝 画师标签对比

### Anima (Flux) - 必须加 @

```
@wlop
@ask  
@fu_mi
@big chungus
@sakimichan
```

**注意**: 画师名有空格也要加 @，如 `@big chungus`

### SDXL (Illustrious/Noob) - 不加 @

```
wlop
ask
fu_mi
big_chungus  ← 用下划线连接
sakimichan
```

**注意**: 多词画师名用下划线，如 `big_chungus`

### z-image Turbo - 灵活

```
# 可以用 @
@wlop, @ask

# 可以用自然语言
in the style of wlop
painted by big chungus
```

---

## 🔄 跨模型转换

### Anima → SDXL

```
# Anima
masterpiece, best quality, newest, latest, safe,
@wlop, @ask,
a girl with long silver hair,
1girl, solo, white dress

# SDXL
masterpiece, best quality,
wlop, ask,
1girl, solo, long_hair, silver_hair,
white_dress
```

**转换规则**:
1. 移除 `newest, latest, safe`
2. 画师去掉 `@`，空格改为 `_`
3. 短句拆成 tag
4. 可以添加 LoRA

### Anima → z-image Turbo

```
# Anima
masterpiece, best quality, newest, latest, safe,
@wlop,
a girl with long silver hair and red eyes,
wearing a white dress

# z-image Turbo
一个银发红瞳的女孩穿着白裙子
```

**转换规则**:
1. 简化为核心描述
2. 可以翻译成中文
3. 写成自然语言
4. 移除质量标签

### SDXL → z-image Turbo

```
# SDXL
masterpiece, best quality,
1girl, solo, long_hair, silver_hair, red_eyes,
white_dress, standing, moonlight, night, castle

# z-image Turbo
一个银发红瞳长发女孩，
穿白裙站在月光下，背景是夜晚的城堡
```

**转换规则**:
1. tag 组装成自然句子
2. 可以用中文
3. 添加连接词使其流畅

---

## ❌ 常见错误

### 错误 1: Anima 画师不加 @
```
❌ masterpiece, best quality, wlop, 1girl
✅ masterpiece, best quality, @wlop, 1girl
```

### 错误 2: SDXL 使用复杂句子
```
❌ a beautiful girl with flowing silver hair standing gracefully
✅ 1girl, solo, long_hair, silver_hair, standing
```

### 错误 3: z-image 过度使用质量标签
```
❌ masterpiece, best quality, ultra detailed, high resolution, 一个女孩
✅ 一个银发红瞳的女孩穿着白裙子
```

### 错误 4: Anima/SDXL 使用中文
```
❌ masterpiece, best quality, 一个女孩，长发
✅ masterpiece, best quality, 1girl, solo, long hair
```

---

## 🎯 如何选择？

### 选择 Anima
- ✅ 需要高质量图像
- ✅ 想用英文短句描述
- ✅ 不依赖 LoRA
- ✅ 对画师风格有要求（用 @）

### 选择 SDXL (Illustrious/Noob)
- ✅ 需要使用角色/画风 LoRA
- ✅ 习惯使用 Danbooru tag
- ✅ 需要精确控制
- ✅ 有大量 SDXL LoRA 资源

### 选择 z-image Turbo
- ✅ 想用中文描述
- ✅ 想用自然语言
- ✅ 需要快速预览（4步）
- ✅ 喜欢写长句描述

---

## 📚 相关文档

- [Anima Prompt 指南](./anima-prompt-and-workflow.md)
- [z-image 工作流](./z-image-guide.md)
- [工作流节点映射](./workflow-node-mapping.md)
- [Pretags Draw](../modules/pretags-draw/SKILL.md)
- [Agent 工作流指南](../AGENT_WORKFLOW_GUIDE.md)

---

**最后更新**: 2026-06-08
