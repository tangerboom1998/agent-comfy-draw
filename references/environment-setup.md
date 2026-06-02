# Environment Setup & Directory Layout

## Environment Variables

All paths are configured via environment variables (with sensible defaults). Copy `.env.example` to `.env` and customize as needed.

| Variable | Default | Description |
|---|---|---|
| `LORA_MODEL_DIR` | `/opt/comfyui/models/loras` | LoRA 模型存储根目录 |
| `COMFYUI_ROOT` | `/opt/comfyui/ComfyUI` | ComfyUI 安装根目录 |

Python scripts import `_env.py` to get these values consistently. See project root `_env.py`.

## LoRA File Locations

### Primary storage (organized by model_type → category)

```
$LORA_MODEL_DIR/
├── anima/                  # 默认模型类型 (anima关键字)
│   ├── 人物/               # character LoRAs
│   ├── 服装/               # clothing LoRAs
│   ├── 画风/               # art style LoRAs
│   └── 其他/               # misc LoRAs
├── illustrious&noob/       # noob/illustrious 关键字
│   ├── 人物/
│   ├── 服装/
│   ├── 画风/
│   └── 其他/
├── z_image_turbo/          # turbo/z_image 关键字
│   ├── 人物/
│   ├── 服装/
│   ├── 画风/
│   └── 其他/
├── z-image/                # image-to-image LoRAs
├── z-flux/                 # Flux LoRAs
├── wan/                    # Wan video LoRAs
├── lumina/                 # Lumina LoRAs
├── qwen/                   # Qwen LLM LoRAs
├── qwenedit/               # Qwen Edit LoRAs
└── my_workflows/           # workflow files
```

Model type is auto-detected from LoRA filename via keyword matching. See `_env.py` → `MODEL_TYPE_RULES`.

Default path: `/opt/comfyui/models/loras/`. Override via `LORA_MODEL_DIR` in `.env`.

### Source migration (completed 2026-05-08)
Legacy `/save/models/Lora/sdxl/` was migrated into `loras/`:
- `Act/noob/`, `body/noobIL/`, `Design/noobIL/` → `其他/`
- `clothes/for_ill/` → `服装/`
- `styles/for noob/` → `画风/`
- `Other characters/` → `人物/`
- 3 files with identical hashes were skipped (nai_ILL, nyalia, 13yaoza0)

### ComfyUI loras directory

`$COMFYUI_ROOT/models/loras/` resolves to `$LORA_MODEL_DIR/`. Files in `{model_type}/人物/` subdirectory are accessible to ComfyUI.

**When downloading new LoRAs:** place character LoRAs in `{model_type}/人物/`, style LoRAs in `{model_type}/画风/`, clothing LoRAs in `{model_type}/服装/`. The `model_type` is auto-detected from filename keywords (`_env.py` → `detect_model_type()`).

## pretags.json

### Location
`skills/comfyui-draw/assets/pretags.json` (NOT in the skill root)

### pretags.json Location & Entry Types
`skills/comfyui-draw/assets/pretags.json` (NOT in the skill root)

Categories: `动作`(442), `服装`(828), `镜头`(84), `画风`(305), `场景`(409), `其他`(7972), `人物`(9191)

**Lora=1 counts (as of 2026-05-08):** 人物=280, 服装=188, 画风=35

**人物条目（Lora=1，有模型文件）：**
```json
{
    "cname": "中文名",
    "Source": "来源作品",
    "Lora": 1,
    "model file name": "filename",       // 不含 .safetensors 后缀
    "model hash": 0,
    "unet weight": 0.8,
    "clip weight": 0.8,
    "link": 0,
    "name": "English Name",
    "外貌": "1girl, blue eyes, long hair, ...",
    "服装": 0
}
```

**非人物条目（服装/画风/动作等，Lora=1）：**
```json
{
    "cname": "中文名",
    "Lora": 1,
    "model file name": "filename",
    "model hash": 0,
    "unet weight": 0.8,
    "clip weight": 0.8,
    "link": 0,
    "tag": "english tags, clothing description"
}
```

### Matching Logic
pretags matches files via `model file name` field (strips `.safetensors` suffix). **Not** by hash (most entries have `model hash: 0`). After adding entries, always verify match count = file count.

### Hash Format (when used)
When populated, hashes use **AutoV2 format** — first **10 chars** of SHA256, uppercase. When comparing with CivitAI full SHA256, use prefix matching.

## Batch Pretags Import Workflow

When adding new LoRA files to `人物/` or `服装/`, follow this workflow:

### Step 1: Identify unregistered models
```python
import json, os
from _env import iter_lora_subdirs

with open('assets/pretags.json') as f:
    data = json.load(f)
existing = set()
for k, v in data.get('服装', {}).items():  # or '人物'
    if v.get('Lora') == 1:
        existing.add(v.get('model file name', '').replace('.safetensors', ''))
# 遍历所有 model_type/服装/ 子目录
for lora_dir in iter_lora_subdirs('服装'):
    for fn in os.listdir(lora_dir):
        if fn.endswith('.safetensors') and fn.replace('.safetensors','') not in existing:
            print(f'未注册: {fn}')
```

### Step 2: Read JSON metadata for tags
Each `.safetensors` file may have an accompanying `.json` with `activation text` field — this is the primary tag source for clothing LoRAs.

### Step 3: Compute hash + Civitai lookup (for character models)
```bash
# Compute hash prefix
sha256sum file.safetensors | cut -c1-16

# Lookup on Civitai (use civitai-api skill)
cd skills/civitai-api && python scripts/civitai.py by-hash <hash_prefix>
```
Returns `trainedWords`, `model.name`, `baseModel`. Use `trainedWords` for the `name` field (trigger words).

### Step 4: Create pretags entries — MANDATORY three-field split for 人物
For 服装: `tag` = activation text from JSON, `cname` = filename (or translated).
For 人物: MUST split into three fields:
- `name` = character trigger words from trainedWords (e.g., `rosetta_(nike)`)
- `外貌` = body/appearance tags only (hair, eyes, skin, race, body type, horns, tail, etc.)
- `服装` = clothing/accessory tags (dress, bikini, gloves, tiara, earrings, weapons, etc.)

**NEVER put clothing tags in 外貌.** See SKILL.md "⚠️ 人物条目 Tag 三类拆分规则" for the full classification guide.

**Multi-character models** (e.g., `granblue_fantasy_all`): each character gets its own entry sharing the same `model file name`. Summer/variant costumes are also independent entries.

### Step 5: Verify
```python
# Count models vs pretags entries
files = [f for f in os.listdir(dir) if f.endswith('.safetensors')]
registered = sum(1 for b in bases if b in existing)
print(f'{registered}/{len(files)} matched')
```

## Model Migration Conflict Resolution

When migrating LoRA files between directories, always check for name conflicts first:
1. List `.safetensors` filenames in both source and target
2. For conflicts, compare SHA256 hashes
3. Same hash → skip (keep existing), different hash → rename or ask user

## Multi-Character Model Splitting

When a single LoRA contains multiple characters (e.g., `granblue_fantasy_all` with 50+ characters):
1. Lookup trainedWords via Civitai hash → get all character trigger words
2. Each character = independent pretags entry, all sharing the same `model file name`
3. Summer/variant costume versions are also independent entries (not merged with default)
4. Split tags into name/外貌/服装 per SKILL.md rules
5. If trainedWords only has one generic trigger (e.g., `"all in one"`), keep as single entry

## ComfyUI Service
- Host: configured via `COMFYUI_HOST` env var
- GPU: RTX 4090, 24GB VRAM
- Default model for NSFW: noobaiXLNAIXL (`--model 2`)

## Reference Files
- `references/civitai-lookup-pitfalls.md` — Civitai API proxy issues, hash lookup, multi-character splitting
- `references/environment-setup.md` — this file
