# Anima 模型 Prompt 编写与工作流指南

> 合并自: anima-prompt-guide.md, anima-workflow-guide.md, anima-art-style-switching.md, anima-prompt-adaptation.md, anima-action-prompt-techniques.md

---

## 一、Prompt 编写规范

### 1. 基本规则

#### 大小写 & 分隔符
- **全部小写**，用逗号+空格分隔
- **不要用自然语言句式**，用 tag 堆叠
- 不要用 `.` 句号结尾

#### 推荐正 Prompt 前缀
```
masterpiece, best quality, newest, latest, safe,
```

#### 推荐负 Prompt
```
lowres, worst quality, bad anatomy, bad hands, missing fingers, extra fingers, 
blurry, jpeg artifacts, signature, watermark, username, artist name, 
censored, mosaic, barcode, bar censor,
```

### 2. Tag 顺序（严格按此顺序）

1. **Quality 标签** — `masterpiece, best quality, newest, latest`
2. **Safety 标签** — `safe,`（或 `nsfw,` 见下方）
3. **Artist 标签** — `@artist_name`
4. **Genre/Style 标签** — 画风/流派
5. **角色描述** — 姓名、外貌、服装
6. **动作/姿势**
7. **场景/背景**
8. **光影/氛围**
9. **技术标签** — `1girl,` `solo,` 等

示例：
```
masterpiece, best quality, newest, latest, safe, @wlop, 
1girl, solo, silver hair, long hair, red eyes, 
white dress, standing, looking at viewer, 
castle background, moonlight, night sky, 
dreamlike atmosphere, soft lighting,
```

### 3. Quality 标签

| 用途 | 标签 |
|------|------|
| 必备前缀 | `masterpiece, best quality,` |
| 额外增强 | `newest, latest, high quality, amazing quality,` |
| 避免使用 | `nsfw, explicit` 等（会触发 ComfyUI 安全过滤） |

### 4. Safety 标签（必须加！）

- **SFW 图**：前缀加 `safe,`
- **NSFW 图**：前缀加 `nsfw,` 但要注意 ComfyUI 可能有文本过滤（见 nsfw-prompt-bypass.md）

### 5. Artist 标签

格式：`@artist_name`（小写，下划线连接）

常用画师：
- `@wlop` — 唯美幻想风
- `@ask` — 精美日系
- `@fu_mi` — 性感厚涂
- 更多画师参考下方"艺术风格切换"章节

### 6. 敏感/情色内容专有 Tag

| 类别 | 推荐 tag |
|------|----------|
| 全裸 | `completely nude,` |
| 半裸 | `topless,` `bottomless,` |
| 露出 | `exposed,` `revealing,` |
| 性器官 | `pussy,` `nipples,` `anus,` `penis,` |
| 性行为 | `sex,` `vaginal,` `fellatio,` `paizuri,` |

### 7. 常见错误

| 错误 | 正确做法 |
|------|----------|
| 自然语言描述 | Tag 堆叠 |
| 中文 prompt | 全英文 tag |
| 大写字母 | 全部小写 |
| 句号结尾 | 无标点结尾 |
| 忘记 safe/nsfw 标签 | 必须加前缀 |
| SDXL 风格长句 | Anima 只用 tag |

### 8. 自然语言混合

Anima 支持 **有限的自然语言** 作为 tag 补充，但不推荐超过 20% 占比：

```
...tags..., (a quiet forest at dawn:1.2), ...more tags...
```

### 9. Weight 加权

格式：`(tag:1.2)` 或 `(tag:1.5)`

```
masterpiece, best quality, safe, @wlop, 1girl, (silver hair:1.3), (red eyes:1.2), ...
```

---

## 二、艺术风格切换技法

### 核心原则
- **保持骨架 prompt 不变**（角色、服装、动作、场景结构）
- **只替换风格相关的 tag 层**（画师、流派、技法）
- 用同样的 seed/参数并行出多版本对比

### 分类 A：画师标签（`@artist` 前缀）

| 画师 | 风格特点 |
|------|----------|
| `@wlop` | 唯美幻想，厚涂光影 |
| `@ask` | 精美日系，柔和配色 |
| `@fu_mi` | 性感厚涂，温暖色调 |
| `@kedama_milk` | 可爱Q版，幼态 |
| `@lack` | 清冷高级感，低饱和度 |
| `@reoenl` | 韩系半写实 |
| `@sciamano240` | 极致精细，高细节 |
| `@sakimichan` | 唯美厚涂 |
| `@greem_bang` | 韩系纯爱 |
| `@cacao` | 油画厚涂 |
| `@hiten` | 纯爱唯美 |
| `@mochi_icecream` | Q版可爱 |

### 分类 B：流派/技法标签（不加 @）

- `watercolor,` `oil painting,` `ink wash,`
- `flat color,` `cel shading,` `thick paint,`
- `sketch,` `line art,` `monochrome,`
- `photorealistic,` `semi-realistic,`

### 分类 C：混合用法

```
@wlop, watercolor, ink wash, thick paint,
```

### 风格选择偏好
- 公子偏好：唯美、质感、不外露骨骼/解剖结构
- 避免：过于平面化、简笔画风、过度解剖展示

---

## 三、Prompt 骨架映射法（适配不同角色/场景）

### 核心思想
保持 prompt 的 **结构骨架**（构图、动作、光影、场景布局），只替换 **内容层**（角色、服装、主题元素）。

### 模板骨架结构

```
[quality tags] [safety] [artist]
[角色身份: 物种+名字+外貌tag]
[服装: 类型+颜色+材质]
[动作/姿势: 空间位置+身体状态]
[场景/背景: 环境+时间]
[光影/氛围: 光源+色调+气氛]
[技术标签: 人数+取景+比例]
```

### 映射示例：暗黑骑士 → 修仙仙子

| 骨架层 | 原始（暗黑无头骑士） | 映射后（修仙仙子施法） |
|--------|---------------------|----------------------|
| 角色身份 | headless dullahan, black armor | celestial maiden, flowing silk robe |
| 服装 | black full plate armor, tattered cape | white and gold hanfu, floating ribbons |
| 动作 | holding own severed head, riding black horse | casting spell, palms glowing, floating midair |
| 场景 | dark forest, full moon, misty graveyard | mountain peak, cloud sea, full moon, lotus pond |
| 光影 | cold moonlight, deep shadows | golden glow from palms, soft moonlight |
| 氛围 | dark fantasy, gothic horror | xianxia immortal, ethereal divine |

### 必须包含
- 角色身份 tag（物种+名字）
- 空间位置关系（x behind y, x in front of y）
- 光源方向（light from left/above）

### 绝对避免
- 改动作后不调空间描述 → 角色错位
- 中文描述混入英文 prompt
- 忽略 safety 标签

---

## 四、动作 Prompt 技法

### 1. 掀裙子 (Skirt Lift)

核心 tag 组合：
```
skirt lift, holding skirt, lifting skirt, exposing panties, 
upskirt, looking back, behind view
```

推荐画师：`@fu_mi, @reoenl`

### 2. 直接露出 (Explicit Exposure)

核心 tag：
```
spread legs, presenting pussy, spreading pussy, 
close-up, looking at viewer, explicit,
```

### 3. 意外走光 (Accidental Exposure)

核心 tag：
```
wind lift, skirt caught, falling, slipping, 
unaware, embarrassed, blushing,
```

### 4. 坐骑/骑乘 (Mounting/Riding)

核心 tag：
```
riding, straddling, cowgirl position, on top,
looking down, hands on chest, intimate,
```

---

## 五、工作流使用指南

### 工作流文件
- **Anima 专用**：`anima-new-Latent.json`（技能根目录）
- 指定方式：设置环境变量 `COMFYUI_WORKFLOW_PATH` 指向该文件

### 节点结构

| Node ID | 类型 | 功能 |
|---------|------|------|
| 39 | UNETLoader | 加载 Anima 模型 |
| 38 | CLIPLoader | 加载 CLIP 模型 |
| 37 | CLIPTextEncode | 正 Prompt 编码 |
| 30 | KSampler | 主采样 |
| 50 | FaceDetailer | 面部修复管线 |
| 31 | VAEDecode | latent → 图像 |
| 44/45 | PreviewImage/SaveImage | 输出节点 |

### 与 NoobAI 主工作流对比

| 特性 | Anima | NoobAI |
|------|-------|--------|
| 模型类型 | Qwen CLIP | SDXL |
| Prompt 格式 | 小写 tag | 自然语言+tag |
| 负 Prompt | 必需 | 可选 |
| 模型加载 | UNETLoader | CheckpointLoader |
| FaceDetailer | 内置（节点 50） | 内置 |

### 快速提交

```bash
# 完整流程
python comfyui_draw.py --prompt "masterpiece, best quality, safe, @wlop, 1girl, ..."
```

### 参数建议
- 测试步数：`steps=20, cfg=5`
- 正式图：`steps=30-40, cfg=6-7`
- Seed: 随机（`seed=0`）

### 放大功能

Anima 工作流内置 **CR Upscale Image** 管线（节点 67-76），使用 `4x-UltraSharp` 模型。

#### 放大方式优先级

1. **Native-Res Upscale**（推荐）：直接调大 Latent 尺寸
   ```python
   workflow["13"]["inputs"]["width"] = 2048
   workflow["13"]["inputs"]["height"] = 3072
   ```

2. **Hires.fix 模式**：`return_with_leftover_noise` + 增大步数
   ```python
   workflow["30"]["inputs"]["denoise"] = 0.6
   ```

3. **FaceDetailer 局部放大**：自动处理面部

4. **后处理放大**：使用 `4x-UltraSharp` 独立放大（仅作补充）

### 输出文件规则

| 文件 | 说明 |
|------|------|
| `CCUI_xxx_0.png` | 原始生成图 |
| `CCUI_xxx_2.epng` | FaceDetailer 处理后（加密PNG） |

### 已知陷阱

1. **模型路径问题**：UNETLoader 需要正确的模型路径
2. **连接问题**：确保 ComfyUI 服务已启动
3. **Prompt 硬编码**：注意工作流中可能已有硬编码 prompt 节点
4. **步数/CFG**：Anima 对参数敏感，测试阶段用低步数

---

## 六、模型兼容性

- **基础模型**：anima_baseV10
- **CLIP 模型**：Qwen CLIP（qwen_3_4b）
- **LoRA 兼容**：需使用 Anima 兼容的 LoRA

---

## 最佳实践

1. 测试阶段用低步数（20 步），确定 prompt 后再提高
2. 每次只改一个变量（画师/风格/safety/动作）
3. 并行提交多个 variant，统一 seed 对比
4. 记录有效组合到笔记
5. 负 prompt 统一使用推荐模板
