---
name: artstyle-test
description: 画风 LoRA 实测评估 — 用 comfyui-draw 生图 → vision 反推画风特征 → 写入 pretags 描述。描述必须来自本地生图实测，禁止直接用 Civitai API 抓下来的 description/trainedWords 作为画风描述。
triggers:
  - 画风测试
  - 画风评估
  - 测画风
  - artstyle test
  - 评估画风
env:
  required:
    - COMFYUI_HOST: "ComfyUI 服务地址（例如：http://127.0.0.1:8188）"
  optional:
    - CONDA_PATH: "Conda 安装路径（例如：/path/to/anaconda3）"
    - CONDA_ENV: "Conda 环境名（例如：comfy311）"
    - LORA_MODEL_DIR: "LoRA 模型根目录（例如：/path/to/ComfyUI/models/loras）"
---

# artstyle-test — 画风 LoRA 实测评估

## 核心原则

**画风描述必须来自本地生图实测，禁止直接搬运 Civitai API 的 description / trainedWords。**

原因：
- Civitai 上的描述是上传者写的，不一定准确反映实际画风效果
- 不同 checkpoint + 不同 cfg + 不同权重下，同一个 LoRA 效果差异很大
- 只有实际生成 → vision 分析，才能得到可靠的画风描述

## 工作流程

### Step 1: 确定待测画风

从 pretags.json 中查画风记录，获取：
- `name` — 画风名
- `模型名` — LoRA 文件名（不带路径和后缀）
- `画风描述` — 当前描述（可能为空，需要实测覆盖）

```bash
# 查看待测画风数量
python -c "
import json, os
pretags_path = os.getenv('PRETAGS_DATA_PATH', './Tanger-Presets-Show/data/pretags.json')
with open(pretags_path) as f:
    data = json.load(f)
artstyles = data.get('画风', {})
total = len(artstyles)
empty = sum(1 for v in artstyles.values() if not v.get('画风描述'))
print(f'画风总数: {total}, 待测: {empty}, 已测: {total-empty}')
"
```

### Step 2: 生图测试

用 comfyui-draw 生成测试图。两种方式：

**方式 A：纯提示词（推荐，画风特征更纯粹）**

固定通用 base prompt，只变 LoRA：

```bash
BASE_PROMPT="1girl, solo, long hair, blue eyes, white dress, standing, outdoors, sunlight, detailed background, cherry blossoms"
ARTSTYLE_LORA="<lora:FILENAME:0.8:0.8>"

python ./modules/pretags-draw/scripts/comfyui_draw.py \
  "${BASE_PROMPT}, ${ARTSTYLE_LORA}" \
  --host $COMFYUI_HOST \
  --canvas 竖图 --model 2 --cfg 5.5
```

**方式 B：深度图 ControlNet 参考（保持构图一致，对比画风差异）**

用同一张参考图的深度结构约束所有画风测试，构图相同只变画风：

```bash
python ./modules/pretags-draw/scripts/comfyui_draw.py \
  "${BASE_PROMPT}, ${ARTSTYLE_LORA}" \
  --host $COMFYUI_HOST \
  --canvas 竖图 --model 2 --cfg 5.5 \
  --controlnet-image /path/to/reference.png \
  --controlnet-type depth --controlnet-strength 0.5
```

**参数选择：**
- `--model 2` — SDXL 类画风 LoRA 用 steps=8 模型；Wan 类用 `--model 10`
- `--cfg 5.5` — 中等 cfg，避免过高导致画风被压制或过低导致不跟随
- `--canvas 竖图` — 标准竖图方便对比
- LoRA 权重 0.8（unet 和 clip 均为 0.8）— 平衡画风表现和基础质量

> ⚠️ **LoRA 格式必须用 `<lora:filename:unet:clip>`，不能省略 clip 权重！**
> 正确: `<lora:琉音-noob-Tanger:0.8:0.8>`
> 错误: `<lora:琉音-noob-Tanger:0.8>` 或 `<lora:琉音-noob-Tanger>`
> 缺少 clip 权重会导致 LoRA 无法正确加载，生成的图不反映画风特征。2026-05 因此格式错误重跑了全部 298 个画风。
>
> **路径问题：** 如果 stem 名匹配失败（日志 `Auto Load lora None`），改用完整相对路径：
> `<lora:画风/jijia-gnoobv-000014.safetensors:0.8:0.8>`。详见 `comfyui-draw/references/lora-path-resolution-pitfall.md`。
> 2026-05-11 批量重跑中 stem 名均可正常工作，但若遇到 LoRA 未加载，优先检查路径。

### Step 3: Vision 分析画风

对生成的图用 vision 分析，提取画风特征：

```
分析这张图片的画风特征，用中文描述：
1. 线条风格（粗细、硬朗/柔和、轮廓清晰度）
2. 上色风格（厚涂/赛璐璐/水彩/平涂、色彩饱和度、渐变方式）
3. 光影特征（光源方向、明暗对比度、阴影风格）
4. 面部/人体画法（五官比例、眼睛风格、体型特征）
5. 背景处理（精细度、虚实、氛围感）
6. 整体质感（纸张感/CG感/手绘感、颗粒感、锐利度）
7. 类似风格参考（像哪个画师/作品系列）
```

### Step 4: 撰写画风描述

根据 vision 分析结果，写一段 **简洁、准确、可区分** 的画风描述：

**好描述示例：**
- "厚涂赛璐璐混合风，线条粗犷有力，阴影层次丰富，色彩饱和度高，面部偏写实，眼睛细节精致，背景厚涂氛围感强"
- "日系清新平涂，线条纤细柔和，色彩淡雅低饱和，光影柔和，面部圆润可爱，大面积留白，水彩质感"

**坏描述（禁止）：**
- 直接复制 Civitai description
- "这是一个高质量的画风 LoRA"（废话）
- "适合各种场景"（不可区分）

**描述长度：** 30~80 字中文，覆盖 2~3 个最显著的画风特征即可。

### Step 5: 写回 pretags.json

```bash
python -c "
import json, os
PRETAGS = os.getenv('PRETAGS_DATA_PATH', './Tanger-Presets-Show/data/pretags.json')
with open(PRETAGS) as f:
    data = json.load(f)
# 更新描述
name = '画风名'
desc = '写好的画风描述'
if name in data.get('画风', {}):
    data['画风'][name]['画风描述'] = desc
    with open(PRETAGS, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'✅ 已更新 {name}')
"
```

### Step 6: 批量重跑（大规模）

当需要重跑大量画风时，使用批量脚本：

```bash
# 批量生成测试图（正确 LoRA 格式）
python ./tools/artstyle-test/scripts/artstyle_rerun.py --start 0 --limit 15  # 每批 15 个
```

批量流程：生图 → delegate_task 并行 vision 分析（每组 5 张）→ 写入 pretags.json。

脚本路径：[`artstyle-test/scripts/artstyle_rerun.py`](artstyle-test/scripts/artstyle_rerun.py:1)

## 批量测试流程

当需要测试多个画风时：

1. 查出所有 `画风描述` 为空的画风记录（pretags.json → `画风` 对象）
2. 逐个生图（每次只挂 1 个 LoRA，格式 `<lora:filename:0.8:0.8>`）
3. vision 分析 → 写描述 → 写入 pretags.json
4. 每完成一个打日志，失败的记录下来后续重试
5. 4 个模型文件不存在的画风自动跳过：影子人、像素1、像素2、doll

```bash
# 查询待测数量
python -c "
import json, os
pretags_path = os.getenv('PRETAGS_DATA_PATH', './Tanger-Presets-Show/data/pretags.json')
with open(pretags_path) as f:
    data = json.load(f)
artstyles = data.get('画风', {})
total = len(artstyles)
empty = sum(1 for v in artstyles.values() if not v.get('画风描述'))
print(f'画风总数: {total}, 待测: {empty}, 已测: {total-empty}')
"
```

## 常见问题

### Vision 分析被拦截（NSFW）
生成 NSFW 内容时 `vision_analyze` 返回 `"rejected because it was considered high risk"`。此时无法自动评测，需要公子人工看图判断画风特征后手动描述。批量测试时尽量用 SFW 的 base prompt 避免此问题。

### LoRA 文件不存在
有些画风 LoRA 可能只有 pretags 记录但文件已被清理。检查 `lora_file` 路径是否存在：
```bash
# 使用环境变量配置的 LoRA 目录
ls -la "$LORA_MODEL_DIR/画风/FILENAME.safetensors"
```
跳过不存在的，标记为 `description='[文件缺失]'`。

### 效果不明显
权重太低或 base prompt 太复杂会稀释画风效果：
- 权重从 0.8 提到 1.0
- base prompt 简化为 `1girl, solo, white background` 减少干扰

### Wan 类画风
如果 LoRA 文件在 `画风/wan/` 子目录，用 `--model 10`（12步）并加 `wan2.1` 触发词。

## 相关技能

- `comfyui-draw` — 生图工具
- `pretags-batch-import` — pretags 入库流程
- `civitai-api` — 用于获取模型元数据（hash、版本信息），但**不用于获取画风描述**
