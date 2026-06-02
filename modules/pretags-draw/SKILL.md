---
name: comfyui-draw
description: "AI 绘画工具：通过 ComfyUI API 生成图片。内置中文提示词处理引擎（tag_producer），支持中文关键词自动转换为 SDXL 英文 tag、LoRA 调用格式 <lora:LoraName:unet:clip>、画师串随机抽取、多种画布预设、多种采样器、模型切换。生成完成后图片会自动发送给用户。核心工作流：Agent构建→tag_producer→Agent翻译增强+12项质量自检→生图+发送。发图 Discord 用 MEDIA 路径（Docker 沙箱需用宿主机路径）。每次 find 确认路径(CWD/output/CCUI_*.png)，忽略 .epng。tag_producer 缺 numpy/pandas 时报错可见。"
metadata: {"nanobot":{"emoji":"🎨","requires":{"env":["COMFYUI_HOST"]}},"openclaw":{"emoji":"🎨","requires":{"env":["COMFYUI_HOST"]}}}
---

# ComfyUI Draw

通过 ComfyUI API 生成 AI 图片，内置中文提示词处理引擎。

---

## 🎯 核心工作流（4 步）

```
用户需求 → [Step 1] Agent构建初始prompt → [Step 2] tag_producer处理预设
        → [Step 3] Agent翻译+增强+12项自检 → [Step 4] 生图+发送
```

### Step 1 — 构建初始提示词

### Step 1 — 构建初始提示词

**⚠️ 角色名歧义识别规则（公子纠正 2026-05-18）：**
- 当公子说出中文角色名（如「折枝」「铃」「哲」「柳」），**必须先查 pretags 确认**
- 不要凭字面意思理解（「折枝」不是树枝，是鸣潮角色）
- 快速判断：`python scripts/pretags_manager.py search <关键词>`
- 如果搜索结果中有来源标识（鸣潮/绝区零/原神/崩坏等），按角色处理
- 如果不确定，问公子确认

三种模式：
- **直接传递**：用户给完整英文 prompt → 原样使用
- **预构建传递**：用户给简短中文（如"情趣内衣 骚狐狸精 撸串 4"）→ 传给 tag_producer，Step 3 翻译润色
- **Agent 构建**：用户只说需求 → Agent 按层级构建完整 prompt

**层级结构**：画质 → 画风 → 主体 → 服装 → 表情 → 身材 → 姿势 → 程度 → 暴露 → 镜头 → 场景 → 光影 → 材质 → 画师

### 从 pretags 构建 prompt（手动生图时）

当用 comfyui_draw.py 直接生图而非经过 tag_producer 时，prompt 必须包含 pretags 条目的**所有字段**：

```python
# ✅ 正确：name + tags + appearance + clothing 全用
c = chars['角色名']
tags_part = ', '.join(c.get('tags', []))
name_tag = c.get('name', '')  # 如 "nami (league of legends),"
appearance = c.get('appearance', '')
clothing = c.get('clothing', '')

prompt = f"..., {name_tag} {c.get('groom, ')tags_part}{appearance}{clothing}, ..."
```

**关键规则：`name` 字段不可省略，即使有 LoRA。**
- `has_lora=True`：LoRA 负责身份，但 `name` 仍有辅助作用
- `has_lora=False`：**必须加 `name`**，否则模型不知道画的是谁
- 例如：`娜美-lol` 的 `name="nami (league of legends),` 必须出现

**⚠️ `solo` tag 规则（防止重影/多人物鬼影，公子纠正 2026-05-18）：**
- 所有单角色生图（1girl/1boy/1other）**必须加 `solo` tag**
- 不加 `solo` 时 noobaiXL 模型容易出现重影、双人物、主体边界模糊的鬼影现象
- 即使是全身立绘/白色背景等简单场景也不可省略 `solo`
- 正确示例：`masterpiece, best quality, solo, (zhezhi:1.3), 1girl, ...`

参见 `references/character-preview-generation.md` → ⚠️ 关键陷阱 #0

### Step 2 — tag_producer 预设处理ue`：LoRA 负责身份，但 `name` 仍有辅助作用
- `has_lora=False`：**必须加 `name`**，否则模型不知道画的是谁
- 例如：`娜美-lol` 的 `name="nami (league of legends),` 必须出现

**⚠️ `solo` tag 规则（防止重影/多人物鬼影，公子纠正 2026-05-18）：**
- 所有单角色生图（1girl/1boy/1other）**必须加 `solo` tag**
- 不加 `solo` 时 noobaiXL 模型容易出现重影、双人物、主体边界模糊的鬼影现象
- 即使是全身立绘/白色背景等简单场景也不可省略 `solo`
- 正确示例：`masterpiece, best quality, solo, (zhezhi:1.3), 1girl, ...`

参见 `references/character-preview-generation.md` → ⚠️ 关键陷阱 #0

### Step 2 — tag_producer 预设处理

| 指令 | 示例 | 说明 |
|------|------|------|
| `人物名 [服装] [外貌] [权重]` | `永夜希尔 服装 外貌 0.85` | 查 pretags 生成 tag + LoRA |
| `类别 标签名 [权重]` | `动作 睡觉`、`画风 2d润彩 0.7` | 动作/服装/镜头/画风/场景/其他 |
| `撸串 数量` | `撸串 4` | 随机选取 N 个画师 |

⚠️ 自由中文不会被翻译，原样保留。

### Step 3 — Agent 翻译 + 全面增强 + 自检

1. **翻译**：将自由中文翻译为英文
2. **增强**：按层级重组，补全缺失层次，扩展同类 tag，注入画质前缀，添加权重
3. **12 项自检**：零中文 / 画质 / 主体 / 服装 / 表情 / 身材 / 姿势 / 镜头 / 场景 / 光影 / 权重 / 画师
4. **全英文验证**：`re.findall(r'[\u4e00-\u9fff]+', prompt)` 仅允许"撸串"等预设指令

### Step 4 — 生图 + 发送

```bash
python skills/comfyui-draw/scripts/comfyui_draw.py "全英文prompt" \
  --canvas 竖图 --model 2 --steps 28 --cfg 5.5
```

- 默认不放大，用户要求时才加 `--upscale`
- **Discord 发图：** 在回复文本中写 `MEDIA:/absolute/path/to/file.png`（如 `MEDIA:./output/CCUI_xxx_1.png`），Hermes 自动处理为附件。不要用 `send_message(media_path=)` — DM 中可能静默失败。
- **Docker 沙箱注意路径映射**：容器内 `/workspace/output/` 对应宿主机 `~/.hermes/workspaces/<profile>/output/` — MEDIA 必须用宿主机路径
- 多图时每张完成立即发送，不等全部完成
- 用 `find` 确认路径（CWD/output/CCUI_*.png），忽略 `.epng`

#### 🎯 图片选择规则（公子指定）

`noob_api_fix_upscale_face_detailer.json` 工作流默认输出三张文件：

| 文件编号 | 内容 | 处理 |
|----------|------|------|
| `CCUI_*_0.png` | KSampler 原始输出（无面部修复） | ❌ **不发送** |
| `CCUI_*_1.png` | FaceDetailer 面部修复后的最终图 | ✅ **只发送这一张** |
| `CCUI_*_2.epng` | FESaveEncryptImage 加密格式 | ❌ 忽略 |

**规则（公子要求）：取编号最大的 .png 文件（永远忽略 .epng）。**
- 不走 `--upscale`：发 `_1.png`（FaceDetailer 输出）
- 走了 `--upscale`：可能有 `_3.png`/`_4.png`（放大+二次面部修复），发最后一个 .png
- 永远不发 `_0.png`（那是 KSampler 的原始裸输出）

⚠️ **发图方式：** 在回复文本中直接写 `MEDIA:/absolute/path/to/CCUI_xxx_1.png`，Hermes 会自动处理为 Discord 附件。不要用 `send_message(media_path=)` — 该参数在 DM 中可能静默失败。

---

## ⚠️ 关键格式规范

### LoRA 格式（绝对不能省略 lora: 前缀）

**⚠️ FEEncLoraAutoLoader（noobaiXL 工作流）不需要子目录前缀，也不带 .safetensors 后缀。**

公子确认的格式（仅文件名，无后缀，无目录）：
```
✅ <lora:露帕-Lupa:0.8:0.8>
✅ <lora:琪亚娜kiana-young:0.8:0.8>
✅ <lora:琉音-noob-Tanger:0.8:0.8>
❌ <lora:露帕-Lupa.safetensors:0.8:0.8>  ← 不要 .safetensors 后缀
❌ <lora:人物/露帕-Lupa:0.8:0.8>  ← 不要子目录前缀
❌ <琉音-noob-Tanger:0.8:0.8>  ← 缺 lora: 前缀，无效！
```

**FEEncLoraAutoLoader 搜索逻辑：** 递归搜索 `models/loras/` 目录下所有子目录，仅按文件名匹配。所以直接写文件名即可——无目录前缀，无后缀。

**规则：** `FEEncLoraAutoLoader` 会递归搜索 `models/loras/` 目录下所有子目录，直接写文件名即可，不需要加子目录路径前缀。

### SDXL 权重格式（必须括号包裹）
```
✅ (keyword:1.3)
❌ keyword:1.3  ← 裸权重，不稳定
```

### Host URL（必须含 http://）
```
✅ --host http://127.0.0.1:8892
❌ --host 127.0.0.1:8892  ← 缺协议前缀，静默失败
```

---

## ⚠️ Top 5 陷阱

| # | 陷阱 | 症状 | 修复 |
|---|------|------|------|
| 1 | **中文未翻译** | 生成随机/崩坏内容 | Step 3 全英文验证不可跳过 |
| 2 | **LoRA 缺 lora: 前缀** | LoRA 静默不加载 | 每次生图前验证格式 |
| 3 | **host 缺 http://** | 连接失败但报错不明确 | 显式传完整 URL |
| 4 | **路径 ≠ skills/comfyui-draw/output** | 文件不存在 | 用 find 确认实际路径 |
| 5 | **.epng 加密格式** | 混淆输出文件 | 忽略 .epng，只用 .png |
| 6 | **vision 模型不支持该模型** | vision_analyze 返回 400 | 当前 provider (deepseek-v4-flash) 不支持 image_url，生图后直接用 MEDIA 发图给用户，不要尝试 vision 验证 |
|| 7 | **大批次后台超时** | batch_preview_gen.py 跑一半退出码 143 (SIGTERM) | Hermes background=true 有 ~3-5 分钟超时。改用 nohup + 日志重定向（详见 `references/character-preview-generation.md` 陷阱 #6） |
|| 8 | **send_message 发图失败** | 用户说没收到图片 | 见下方「发图失败原因与正确做法」 |

---

## 📤 发图失败原因与正确做法（2026-05-20 总结）

### 失败原因分析

| 原因 | 现象 | 出现次数 |
|------|------|----------|
| `send_message` 需要 `target` 参数 | 调用时报错 "Both 'target' and 'message' are required" | 多次 |
| Discord 文件上传可能超时/静默失败 | API 返回 success 但用户端没收到 | 多次 |
| `MEDIA:` 路径在回复中有时不生效 | 直接写在 message 里用户也收不到 | 偶发 |

### ✅ 正确做法（按优先级）

**方法 1：直接在回复中用 MEDIA: 路径（推荐）**
```
公子，图片已生成——

MEDIA:./output/CCUI_xxx_1.png
```
- 不需要调用 send_message
- 直接写在助手回复中，Hermes 自动处理
- 路径必须是**绝对路径**

**方法 2：如果方法 1 不生效，用 send_message**
```python
send_message(
    target="discord:tanger0847",  # 必须指定 target
    message="图片描述",
    media_path="/absolute/path/to/image.png"
)
```
- 必须同时提供 `target` + `message` + `media_path`
- `media_path` 必须是绝对路径

**方法 3：如果以上都不行，用 vision_analyze 先加载图片**
```python
# 先用 vision 加载（即使不分析内容）
vision_analyze(image_url="/absolute/path/to/image.png", question="描述图片")
# 然后在回复中用 MEDIA:
```

### ⚠️ 关键注意点

1. **路径必须是绝对路径**：
   - ✅ `./output/CCUI_xxx_1.png`
   - ❌ `output/CCUI_xxx_1.png`（相对路径不生效）

2. **只发 FaceDetailer 修复后的图**：
   - `_0.png` = KSampler 原始输出 → ❌ 不发
   - `_1.png` = FaceDetailer 修复后 → ✅ 只发这个
   - `_2.epng` = 加密格式 → ❌ 忽略

3. **先确认文件存在**：
   ```bash
   ls -la ./output/CCUI_xxx_1.png
   ```

4. **如果用户说没收到，立即用 MEDIA: 重发**，不要重复用 send_message

---

## 🔬 功能验证与测试

首次使用或环境变更后，用 3 步快速验证：

### Step 1 — 环境连接检查

```bash
echo "COMFYUI_HOST=$COMFYUI_HOST"
curl -s --connect-timeout 5 $COMFYUI_HOST/system_stats | python3 -m json.tool
```

预期：看到 `comfyui_version`, `cuda:0 NVIDIA GeForce RTX 4090`, `vram_free` > 2GB。

### Step 2 — tag_producer CLI 验证

```bash
cd .

# 画风预设有匹配，应输出 LoRA + 画师
python scripts/tag_producer.py "画风 2d润彩,撸串 3"
# → 输出: <lora:jijia-gnoobv-000014:0.5:0.5>,masterpiece,...,artist:...  ✅

# 未匹配中文不会翻译，原样保留
python scripts/tag_producer.py "白毛 狐耳 红瞳 古风 妖媚,撸串 4"
# → 中文原样保留 + 4 位随机画师  ✅

# 预设不存在的指令返回空（不报错）
python scripts/tag_producer.py "动作 站立"
python scripts/tag_producer.py "场景 月夜"
# → 返回空字符串（可接受行为） ✅
```

**tag_producer 关键 API（Python 调用）:**  
- 便捷函数：`from scripts.tag_producer import process_prompt` → `process_prompt("画风 2d润彩")`  
- 实例方法：`TagProducer(Settings()).tagrep("画风 2d润彩")`  
- CLI 入口：`python scripts/tag_producer.py "prompt"`（解析 sys.argv）  
- **无 `process()` 方法**，注意不要调错名。`tagrep()` 是主处理方法。

### Step 3 — 端到端生图测试

```bash
cd .

TAG_OUT=$(python scripts/tag_producer.py "画风 2d润彩,撸串 3" 2>&1 | grep "^输出:" | sed 's/^输出: //')
FULL_PROMPT="masterpiece, best quality, (1girl:1.2), white hair, fox ears, red eyes, $TAG_OUT"
python scripts/comfyui_draw.py "$FULL_PROMPT" --model 2 --steps 20 --cfg 5.5 --canvas 竖图 --seed 42
```

预期：
- 输出 `ComfyUI prompt 已提交: <uuid>` → `生成中...` → `图片已保存: output/CCUI_*.png`
- 约 10-15 秒返回
- 找到文件：`find output/ -name "CCUI_*.png"`，忽略 `.epng`

### ⚠️ Vision 验证限制

当前 profile 使用的 provider (deepseek-v4-flash) 不支持 vision/image_url 请求。生图后：
- **不要**调用 `vision_analyze` 验证图片内容
- **直接**用 `MEDIA:/absolute/path` 发图给用户
- 图片路径示例：`./output/CCUI_*.png`

---

## CLI 参数速查

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--canvas` | 竖图 | 竖图/横图/方图 |
| `--model` | 1 | 1=tamix_ninini_v4（默认）, 2=noobaiXL |
| `--steps` | 28 | 采样步数 |
| `--cfg` | 5.5 | CFG 引导强度 |
| `--upscale` | off | 启用放大 |
| `--controlnet-image` | 空 | ControlNet 参考图路径 |
| `--controlnet-strength` | 0.8 | ControlNet 强度 |
| `--controlnet-type` | auto | 预处理类型（lineart/canny/depth/pose等） |

采样器：0=euler, 1=euler_ancestral(默认), 7=dpmpp_2s_ancestral, 9=dpmpp_2m, 14=ddim

---

## 中文预设指令

```
人物名 [服装] [外貌] [权重]     # 永夜希尔 服装 外貌 0.85
类别 标签名 [权重]              # 动作 睡觉、画风 2d润彩 0.7
随机 [游戏名] [服装] [外貌]     # 随机 绝区零 外貌
撸串 数量                       # 撸串 4（随机画师）
```

---

## 画风 LoRA 速查

路径：`$LORA_MODEL_DIR/画风/`

格式：`<lora:画风/filename.safetensors:weight:clip_weight>`

| 文件 | 风格 | 权重 |
|------|------|------|
| testink5_1.safetensors | 水墨笔触 | 0.6 |
| dark_comic_fantasy_*.safetensors | 暗黑漫画 | 0.6 |
| ILwatercolor.safetensors | 水彩 | 0.6 |
| lightingSlider.safetensors | 光影增强 | 0.4 |

⚠️ 风格 LoRA 权重 ≥0.4 会导致手指畸变！建议 ≤0.3。

---

## ControlNet 速查

```bash
python comfyui_draw.py "prompt" --model 2 \
  --controlnet-image /path/to/ref.png \
  --controlnet-type lineart --controlnet-strength 0.6
```

类型：auto(线稿) / lineart / canny / depth / pose / scribble / hed / normal / color / manga

深度图默认 strength=0.5，其他默认 0.8。

---

## z-image turbo（非 SDXL 工作流）

⚠️ z-image turbo 是独立推理管线，不能用 comfyui_draw.py 默认工作流。

- 模型：`z_image_turbo_bf16.safetensors` + `qwen_3_4b.safetensors`
- Steps=4, CFG=1, Sampler=res_multistep, Scheduler=simple
- 支持中文 prompt，不需要 masterpiece 前缀
- LoRA 路径：`z-image/文件名.safetensors`

详见：`references/z-image-turbo-workflow.md`

---

## 配置

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `COMFYUI_HOST` | `http://127.0.0.1:8188` | ComfyUI 地址 |
| `COMFYUI_WORKFLOW_PATH` | `assets/noob_api_fix_upscale_face_detailer.json` | 工作流模板（默认带 FaceDetailer 面部修复） |
| `COMFYUI_OUTPUT_DIR` | `output` | 输出目录 |

依赖：`pip install aiohttp pandas numpy`

⚠️ Docker 沙箱中（群聊子 profile），镜像默认缺少 aiohttp，首次运行前需 `pip install aiohttp`。
详见 `references/docker-sandbox-comfyui.md`。

---

## 详细参考

| 主题 | 文件 |
|------|------|
| 超现实/幻想 prompt 构建 | `references/creative-prompt-building.md` |
| 狐妖化 prompt 改写 | `references/prompt-foxgirl-adaptation.md` |
| 参考图复刻工作流 | `references/image-replication-workflow.md` |
| 画风测试流程 | `references/artstyle-testing-workflow.md` |
| 画风描述合集 | `references/artstyle_descriptions.md` |
| NSFW 提示词绕过策略 | `references/nsfw-prompt-bypass.md` |
| z-image turbo 详情 | `references/z-image-turbo-workflow.md` |
| z-image LoRA 目录 | `references/z-image-lora-catalog.md` |
| FaceDetailer 管线节点结构 | `references/face-detailer-pipeline.md` |
| 角色预览图生成 | `references/character-preview-generation.md` |
| 角色预览图批量生成 | `references/character-preview-batch-generation.md` |
| LoRA 路径陷阱 | `references/lora-path-resolution-pitfall.md` |
| Host URL 陷阱 | `references/host-url-pitfall.md` |
| Docker 沙箱输出路径陷阱 | `references/docker-sandbox-output-pitfall.md` |
| Docker 沙箱生图 | `references/docker-sandbox-comfyui.md` |
| 浏览器直提交 API | `references/browser-api-direct-submission.md` |
| 多 Profile 同步 | `references/multi-profile-sync.md` |
| Pretags 双路径同步 | references/pretags-dual-path-sync.md |
| Pretags 父条目检测与删除 | references/pretags-parent-entry-detection.md |
| Pretags 管理 | `scripts/pretags_manager.py` |
| 画风测试脚本 | `scripts/artstyle_test.py` |
| 角色预览图批量生成 | `scripts/batch_preview_gen.py` |
| Pretags 导出（当前JSON schema） | `scripts/pretags_export_current.py` |
| Pretags Excel 导出工作流（含旧格式检测） | references/pretags-excel-export-workflow.md |
| Excel → Pretags 合并工具 | scripts/pretags_merge_excel.py |
| 父条目审核 Excel 导出 | `scripts/export_suspects_excel.py` |

## Pretags 管理原则（公子指定）

### 🔒 修改 pretags.json 的规则

1. **不擅自修改 schema。** pretags.json 的原始字段集是固定的（cname/source/name/appearance/clothing/has_lora/lora_file/lora_hash/lora_link/unet_weight/clip_weight/tags/tags_count）。添加新字段（如 `preview`）必须先问公子。
2. **CLI 优先。** 所有 pretags 数据修改走 CLI 直接操作文件，不走 Web API。`POST /api/save-pretags` 会用前端数据完全替换文件，导致 `preview` 等扩展字段丢失。
3. **操作前备份。** 修改前 `cp pretags.json pretags.json.bak`。
4. **公子允许的扩展字段：** `preview`（预览图路径）—— 但只在公子明确允许后添加。

### 备注

如果公子说"不补"、"不要动"、"没让你加"——立即回退修改，不要争辩。

### 多服装角色处理

有些角色（如琪亚娜、katya(尘白禁区)）在 pretags 中有多个条目：父条目和按服装拆分的子条目。

**父条目**的 `appearance`/`tags` 字段混合了多套服装，**绝对不能用于生图**。
详见 `references/pretags-parent-entry-detection.md`（含检测规则、删除流程、实测记录）。

**规则：** 生图/生成预览图前，先搜角色名下有没有按服装拆分的子条目。如不确定，问公子用哪个。

**数据源**：`Tanger-Presets-Show/data/pretags.json`（唯一主文件）  
`assets/pretags.json` → 软链接指向上述文件，兼容旧路径  

### ⚠️ 文件路径规范（必须遵守）

```
skills/comfyui-draw/                    ← 技能根目录（所有操作以此为准）
├── Tanger-Presets-Show/data/pretags.json     ← 唯一本体文件（Master Copy）
├── Tanger-Presets-Show/server.py             ← Web 服务
└── assets/pretags.json                 ← 软链接 → ../Tanger-Presets-Show/data/pretags.json
```

**规则：**
1. 所有路径用**相对路径**（相对于项目根目录）：
   - ✅ `Tanger-Presets-Show/data/pretags.json`
   - ✅ `assets/pretags.json`（软链接，等效于本体）
   - ❌ 绝对路径（不可移植，禁止使用）
2. 修改 pretags 后必须重启 server：
   ```bash
   # 1. 杀掉旧进程
   kill $(ps aux | grep server.py | grep -v grep | awk '{print $2}')
   # 2. 重启（必须从 Tanger-Presets-Show/ 目录启动，因为 server.py 用相对路径）
   cd Tanger-Presets-Show && python3 -u server.py &
   ```

**⚠️ 历史教训：**
- 如果存在多份 pretags.json 副本，server 读取的数据可能与 CLI 修改的数据不一致
- 症状：CLI 显示的数据与 Web 界面不同
- 修复：确认只有一份 Master Copy（`Tanger-Presets-Show/data/pretags.json`），杀掉旧 server 重启

旧 master 备份：`assets/pretags_master_backup_*.json`

### ⚠️ Pretags 数据结构（2026-05-20 变更）

**Key 格式已变更：** characters 的 key 从中文名变为 hash 值

```json
// 旧格式（已过期）
"characters": {
  "弗洛洛": { "cname": "弗洛洛", ... }
}

// 新格式（当前）
"characters": {
  "c23fe569": { "cname": "弗洛洛", "source": "鸣潮", "has_lora": true, ... }
}
```

**遍历时必须使用 `cname` 字段作为显示名：**
```python
# ✅ 正确
for key, info in chars.items():
    display_name = info.get('cname', key)  # 用 cname，不用 key

# ❌ 错误
for key, info in chars.items():
    print(key)  # 会输出 hash，如 "c23fe569"
```

**文件名处理：** 预览图等文件名需清理特殊字符
```python
def safe_filename(name):
    return name.replace('/', '_').replace('\\', '_').replace(':', '_')
```

### Excel 导出

pretags.json 数据结构已变更为 characters/categories/series 三层。旧导出脚本 `pretags_export_all.py` **已过期**（schema 不匹配）。

⚠️ 用新脚本导出：

```bash
cd .
python python scripts/pretags_export_current.py tmp/pretags_full_export.xlsx
```

输出 8 个 Sheet（角色/画风/服装/动作/镜头/场景/其他/系列），Lora=1 标绿底，表头冻结+自动筛选。

### CLI 工具

```bash
python pretags stats                    # 统计 (19316角色, 10300标签)
python pretags list [分类]              # 列出分类或条目
python pretags search <关键词>          # 搜索标签/角色
python pretags info <分类> <名称>       # 条目详情
python pretags server start|stop|status # Web 管理界面
python pretags export --format json     # 导出数据
```

Web 管理界面

`http://localhost:8765/index-pretags.html` — 可视化浏览/搜索/增删改

**服务器路径：** `Tanger-Presets-Show/server.py`（与技能目录同级的 Tanger-Presets-Show/ 下）

```bash
# 启动 Web 服务（后台运行）
cd ./Tanger-Presets-Show && python3 -u server.py
```

**⚠️ server.py 已改为相对路径：** 公子手动修改了 server.py，`DATA_PATH` 和 `preview_dir` 现在是相对路径（`data/pretags.json`, `data/character-previews/`），从 Tanger-Presets-Show/ 目录启动会自动解析正确。不要再尝试用绝对路径启动。

### ⚠️ Web 服务启动陷阱

| 陷阱 | 症状 | 修复 |
|------|------|------|
| **旧进程占端口** | 新进程启动后 curl 超时（HTTP 连接成功但无响应） | `kill -9 $(ps aux \| grep server.py \| grep -v grep \| awk '{print $2}')` 清所有旧进程再重启 |
| **启动慢** | 首次 curl 超时（需等待 5+ 秒才响应） | server.py 每次请求重新读取 20MB pretags.json，加载后后续请求快速。首次连接耐心等 5-10 秒 |
| **bash -lic 启动开销** | 使用 background=true 启动时，bash -lic 加载环境变量增加延迟 | 加 `-u` 参数（`python3 -u server.py`）确保 stdout 能及时输出 |
| **⚠️ 两份 pretags.json 路径不同** | server 读的是旧数据，CLI 查的是新数据，两边数据不一致 | **根源：** 如果项目存在多份副本，server 和 CLI 可能操作不同文件。**修复：** 确保只有一份 Master Copy（`Tanger-Presets-Show/data/pretags.json`），CLI 修改后 kill+restart server。详见 `references/pretags-dual-path-sync.md` |
| **⚠️ server 会覆盖 CLI 数据修改** | CLI 删除/修改条目后，server.py 仍在运行，其 Web 端保存（POST /api/save-pretags）会用浏览器中缓存的旧数据完全覆盖 pretags.json，导致 CLI 改动静默丢失 | **正确顺序：** `kill server → CLI 修改 → restart server`。删除父条目后务必重启 server 才能生效。详见 `references/pretags-parent-entry-detection.md` 中的"删除后 server 覆盖陷阱" |
| **kill 无效** | `kill <PID>` 后进程仍在（`ps aux` 还能看到） | 改用 `kill -9 <PID>` 强制杀掉。检查是否有 shell wrapper 进程（`/bin/sh -c ...`）也需要一并杀掉 |

支持功能：按分类浏览、搜索筛选、LoRA 筛选、卡片增删改、补录预览图

### 角色预览图

**现状（2026-05-17）：** 总角色 19,314 个，有 LoRA 的 485 个，但只有 **3 张**预览图。

预览图存放目录：`Tanger-Presets-Show/data/character-previews/`
命名格式：`角色名__来源.jpg`（如 `尤诺__鸣潮.jpg`）

生成 + 上传流程详见 `references/character-preview-generation.md`

**批量生成脚本：** `scripts/gen_character_previews.py`
```bash
# 检查缺失预览图
python scripts/gen_character_previews.py --check

# 全部生成
python scripts/gen_character_previews.py

# 只生成 10 个
python scripts/gen_character_previews.py --limit 10

# 只生成指定角色（模糊匹配）
python scripts/gen_character_previews.py --name 弗洛洛
```

**立绘模板：**
```
masterpiece, best quality, ultra-detailed, very aesthetic, absurdres,
<lora:{lora_file}:{unet_weight}:{clip_weight}>,
solo, {name}, {tags},
full body, standing, white background, simple background,
detailed face, beautiful eyes, looking at viewer
```

#### ⚠️ 人物多服装陷阱

有些角色（如琪亚娜）在 pretags 中有多个条目：

| 条目 | tag 特征 | 适用场景 |
|------|----------|----------|
| `琪亚娜·卡斯兰娜(崩坏三)`（父条目） | appearance 字段混了 12 套衣服的 tag | ❌ 不要用这个生图 |
| `琪亚娜白练` / `琪亚娜月光` / `琪亚娜游侠` 等（子条目） | appearance 只有一套衣服的 tag | ✅ 用这个生预览图 |

**规则：** 生成预览图时，先搜角色名下有没有按服装拆分的子条目（`角色名+服装名`）。如果有，**用子条目**，不要用父条目。父条目的 `appearance` 是所有服装的大杂烩。

#### ⚠️ Web 端保存会丢失 `preview` 字段

`POST /api/save-pretags` 会用 Web 前端发送的数据**完全替换** pretags.json。如果前端数据中没有 `preview` 字段（前端常见 bug），已有预览图数据的角色会丢失 preview。

**最佳做法：** 生成预览图后，用 CLI 直接操作文件，不走 Web API：

```python
import json, os
from PIL import Image

# 1. 复制图片
preview_dir = 'Tanger-Presets-Show/data/character-previews/'
os.makedirs(preview_dir, exist_ok=True)
dst = os.path.join(preview_dir, '角色名__来源.jpg')
Image.open(src_png).convert('RGB').save(dst, 'JPEG', quality=85)

# 2. 更新 pretags.json
data = json.load(open(pretags_path))
data['characters']['角色名']['preview'] = './data/character-previews/角色名__来源.jpg'
json.dump(data, open(pretags_path, 'w'), ensure_ascii=False, indent=2)
```

#### 如何快速找有 LoRA 无预览的角色

```python
candidates = [(k, v) for k, v in chars.items() 
              if v.get('has_lora') and not v.get('preview')]
# 按 tag 数量排序取 tag 最丰富的前 N 个
candidates.sort(key=lambda x: len(x[1].get('tags', [])), reverse=True)
```

### 编程接口

- `scripts/pretags_manager.py` — Python CRUD 接口，agent 可直接调用
- `scripts/tag_producer.py` — 中文→英文 tag 转换引擎
- `Tanger-Presets-Show/server.py` — RESTful API 服务器
