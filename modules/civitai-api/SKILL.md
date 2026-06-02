---
name: civitai-api
description: Full Civitai public REST API skill — search/download/inspect models, versions, images, creators, tags, users; batch hash lookup; vault management; permissions check; enum reference. 21 subcommands covering every public endpoint.
version: 3.1.0
---

# Civitai API (v3 — Complete coverage)

Search, inspect, download, users, vault, permissions — **every public Civitai endpoint**.

## Path Configuration

All paths are configured via environment variables in project root `.env`:

```bash
# LoRA model storage root
# Structure: $LORA_MODEL_DIR/{model_type}/{category}/
#   model_type auto-detected from filename keywords:
#     "noob"/"illustrious" → illustrious&noob/
#     "turbo"/"z_image"    → z_image_turbo/
#     "anima" / default    → anima/
LORA_MODEL_DIR=/opt/comfyui/models/loras

# ComfyUI installation root (used by --comfyui-dir fallback)
COMFYUI_ROOT=/opt/comfyui/ComfyUI
```

`civitai.py download` and `download-model` use `COMFYUI_ROOT` as fallback when `--comfyui-dir` is not specified.

## Quick start

```bash
# Auth (optional; required for NSFW, downloads, vault, me)
CIVITAI_API_KEY=your_token

# ── Search ──
python skills/civitai-api/scripts/civitai.py models --query "noob lora" --nsfw true --limit 5

# ── Download (COMFYUI_ROOT env var provides default --comfyui-dir) ──
python skills/civitai-api/scripts/civitai.py download-model 12345
```

## Full Command Reference (21 commands)

### Search & Inspect (7 commands)

| Command | Endpoint | Auth |
|---------|----------|------|
| `models --query "..."` | GET /models | Public |
| `model <id>` | GET /models/{id} | Public |
| `version <id>` | GET /model-versions/{id} | Mixed |
| `version-mini <id>` | GET /model-versions/mini/{id} | Public | ⚠️ Broken on civitai.red — use `model` instead |
| `creators --query "..."` | GET /creators | Public |
| `tags --query "..."` | GET /tags | Public |
| `images --model-id <id>` | GET /images | Public |

### Host Selection

```bash
python civitai.py --host civitai.com ...   # default
python civitai.py --host civitai.red ...   # mirror domain (better latency from some regions)
```

### Hash Lookup (3 commands)

| Command | Endpoint | Auth | Note |
|---------|----------|------|------|
| `by-hash <hash>` | GET /model-versions/by-hash/{hash} | Public | Auto-fallback: SHA256 → AutoV2 |
| `by-hash-batch "h1,h2,h3"` | POST /model-versions/by-hash | Public | Batch (comma-separated) |
| `by-hash-ids "h1,h2"` | POST /model-versions/by-hash/ids | Public | Batch → IDs only |

`by-hash` accepts full SHA256 (64 chars) and auto-retries with first 10 chars (AutoV2) on 404.

### Download (3 commands)

| Command | What it does |
|---------|-------------|
| `download <version_id>` | Download file by version ID |
| `download-model <model_id>` | Download latest version by model ID |
| `download-url <version_id>` | Print URL only (no download) |

Options: `--output/-o`, `--comfyui-dir`, `--name`, `--prefer`, `--resume`, `--version-name`

### Users (2 commands)

| Command | Endpoint | Auth |
|---------|----------|------|
| `me` | GET /me | **Required** |
| `users --query "..."` | GET /users | Public |

### Permissions (1 command)

| Command | Endpoint | Auth |
|---------|----------|------|
| `permissions --model-id <id>` | GET /permissions/check | Mixed |

### Vault (4 commands) — membership required

| Command | Endpoint | Auth |
|---------|----------|------|
| `vault` | GET /vault/get | **Required** |
| `vault-items` | GET /vault/all | **Required** |
| `vault-check "id1,id2"` | GET /vault/check-vault | **Required** |
| `vault-toggle <version_id>` | POST /vault/toggle-version | **Required** |

### Reference (1 command)

| Command | Endpoint | Auth |
|---------|----------|------|
| `enums` | GET /enums | Public |

Returns all valid values for model types, sort options, periods, etc.

### Common Filters

`--query` `--limit` `--page` `--cursor` `--types` `--sort` `--period` `--tag` `--username` `--nsfw true|false`

## ComfyUI Auto-Placement

When `--comfyui-dir` is set, `download` and `download-model` auto-place files:

| Model Type | Target Directory |
|-----------|-----------------|
| Checkpoint | `models/checkpoints/` |
| LORA / LoCon | `models/loras/` |
| TextualInversion | `models/embeddings/` |
| VAE | `models/vae/` |
| Upscaler | `models/upscale_models/` |
| Controlnet | `models/controlnet/` |

## Download features

- Streaming + progress bar
- Auto .safetensors preference
- Resume interrupted downloads (`--resume`)
- JSON result with path/size/hash

## Workflow examples

```bash
# 1. Search → find model
python ... models --query "illustrious NSFW" --types Checkpoint --nsfw true

# 2. Inspect
python ... model 12345

# 3. Download directly to ComfyUI
python ... download-model 12345 --comfyui-dir "$COMFYUI_ROOT"

# 4. Batch identify local files
python ... by-hash-batch "abc123,def456,ghi789"

# 5. Check who you are
python ... me

# 6. Add to vault (membership needed)
python ... vault-toggle 67890

# 7. Check vault contents
python ... vault-items
```

## Batch Model Import Pipeline

For the complete **discovery → download → tag-split → pretags registration** pipeline, see:

- **`../../tools/pretags-batch-import/SKILL.md`** — master workflow: batch size limits, classification rules, pitfall catalog
- **`../../references/pretags-data-management.md`** — batch migration, hash conflict detection, LoRA download/registration

### Quick batch discovery

```bash
# Scan creator's newest models, check for noob variants
python civitai.py models --username <creator> --sort "Newest" --nsfw true --limit 15

# Check which models already exist locally (hash comparison)
# → must use prefix matching on AutoV2 hashes (see references/hash-comparison.md)

# Download only new ones (uses $LORA_MODEL_DIR for category target, $COMFYUI_ROOT for --comfyui-dir fallback)
python civitai.py download-model <id> --version-name "noob" \
  -o "$LORA_MODEL_DIR/人物/<name>.safetensors"
```

### ⚠️ Tag splitting is MANDATORY

CivitAI `trainedWords` does NOT distinguish appearance from clothing tags. Every import MUST go through manual tag audit — split into `外貌` (body features: race/hair/eyes/horns/tail) and `服装` (wearables: clothes/footwear/gloves/accessories). See `../../tools/pretags-batch-import/SKILL.md` for the classification rulebook.

## Auth

- Public endpoints work without token
- Set `CIVITAI_API_KEY` in `.env` for NSFW, downloads, vault, me
- Or pass `--token` on command line
- Token format: API key from https://civitai.com/user/account → API Keys
- Passed as `Authorization: Bearer <token>` header for JSON API
- Passed as `?token=<token>` query param for download URLs only

## Pitfalls

1. **`urllib` doesn't auto-read proxy env vars** — `curl` uses `https_proxy` automatically, but Python's `urllib.request` does NOT. The script now has explicit `ProxyHandler` support that reads `HTTPS_PROXY → https_proxy → HTTP_PROXY → http_proxy → ALL_PROXY`. If you're behind a proxy and getting empty items/silent region-gating, verify: `echo $https_proxy`. If set and still failing, the proxy may not allow CONNECT to external HTTPS hosts.

2. **Region gating is silent** — CivitAI silently filters NSFW results for requests from restricted regions. The API returns `items: []` with valid `nextCursor` — indistinguishable from "no results". If you see empty items with valid pagination metadata, you're likely region-gated. Use a proxy (pitfall 1) from a non-restricted region.

3. **Token required for NSFW search** — without `CIVITAI_API_KEY`, the `models` command returns only SFW results. With a token but from a restricted region, results are still filtered. Both token AND non-restricted IP are needed for full NSFW access.

4. **`.env` discovery walks up the directory tree** — `load_env_file()` looks for `.env` starting from `scripts/`, going up 6 parent levels. This covers any reasonable profile/workspace layout. If `CIVITAI_API_KEY` isn't being read, pass `--token` explicitly.

5. **`version-mini` → HTTP 404 on civitai.red** — The `/model-versions/mini/{id}` endpoint consistently returns 404 from the civitai.red mirror, even for valid model IDs that appear in search results. **Always use `model <id>` instead** — it returns full version data (files + hashes) and works reliably on both civitai.com and civitai.red. Tested: 13/20 models failed with `version-mini` on civitai.red while `model` succeeded for all.

6. **model file name 必须写 stem** — 写入 pretags.json 时 `model file name` 不能带 `.safetensors` 后缀。带后缀会导致后续扫描永远把已录入条目误判为未录入。

7. **CivitAI by-hash 失败仍应入库** — `Model not found`、SSL EOF、timeout 等不代表模型不应入库。画风目录下默认全是画风模型。hash 正常填（本地 SHA256 前10位），link/tag 填 `"无"`。

8. **SHA256 vs AutoV2 hash comparison** — CivitAI API returns full 64-character SHA256 hashes. But local registries (like `pretags.json`) typically store AutoV2 format (first 10 chars of SHA256). Using `==` to compare will ALWAYS fail. Must use `startswith()` or normalize both to the same format. See `references/hash-comparison.md` for the correct pattern and a reproduction of the failed session where this caused 35 real matches to be missed (all of tanger's noob models were incorrectly reported as "not in local").

9. **civitai.red is unreliable for very new models** — Beyond `version-mini` (pitfall 5), even `model <id>` can return garbled/empty JSON on `.red` for models published in the last few weeks. The `.com` domain is more consistent. Pattern: if `model <id>` on `.red` produces a JSON parse error, immediately retry with `--host civitai.com`. Tested: 4 of 37 recently-published tanger models failed on `.red` but succeeded on `.com`.

10. **Illustrious version naming is not standardized** — Some creators (notably tanger) use `"will"` as the version name for Illustrious variants, not `"ill"`. Before using `--version-name`, always inspect the model's versions first: `python civitai.py model <id> | python3 -c "import json,sys; d=json.load(sys.stdin); [print(f'v{v[\"id\"]} name=\"{v[\"name\"]}\" base={v[\"baseModel\"]}') for v in d.get('modelVersions',[])]"`. Then use the exact string from the `name` field.

11. **Download with `-o` to category subdirectories** — The local model library uses `$LORA_MODEL_DIR/{model_type}/{人物,画风,服装}/` structure. `model_type` is auto-detected from filename keywords (noob/illustrious → `illustrious&noob/`, turbo/z_image → `z_image_turbo/`, anima/default → `anima/`). Always use `-o` to target the correct category directory, not `--comfyui-dir` (which auto-places in a flat `models/loras/`). Character LoRAs go to `{model_type}/人物/`, style LoRAs to `{model_type}/画风/`, clothing LoRAs to `{model_type}/服装/`.

12. **Models deleted from Civitai (HTTP 404)** — When `model <id>` returns `{"error":"No model with id XXXXX"}`, the model has been permanently removed from Civitai. This cannot be recovered. For pretags entries pointing to deleted models:
    - If the `.safetensors` file exists locally → keep the entry, model is still usable
    - If the file is missing → the model is lost. Update pretags with `"link": ""` and note deletion
    - Search Civitai for similar alternatives by keywords (e.g., "pixel art noob illustrious")
    - 2026-05 实例：pixel_art (ID:938369), aic_pixel (ID:946136) 均已下架

13. **Tag mixing in trainedWords** — CivitAI `trainedWords` dumps appearance and clothing tags together with NO classification. Directly copying to pretags WITHOUT splitting causes ALL tags to end up in `外貌` and `服装` left empty (37 entries had this issue on 2026-05-08). Fix: see `../../tools/pretags-batch-import/SKILL.md` for the mandatory manual tag audit process and classification rulebook.

14. **CivitAI model descriptions ≠ 画风描述** — CivitAI API 返回的模型描述（`description` 字段）是作者写的模型说明/版本说明/HTML 富文本，**不得直接写入 pretags 的 `画风描述` 字段**。画风描述的唯一来源是本地生图评测：ComfyUI 出测试图 → vision 分析色调/笔触/光影/质感 → 基于实测撰写。导入时 `画风描述` 留空 `""`，等后续实测补入。

15. **def prefix pollution** — Many models have `Xxxdef TAG`, `Xxxdef,` (bare), and `XxxdefTAG` (merged) prefixes from trigger word + tag concatenation. All must be stripped during Phase 4 tag cleanup. Three distinct formats exist — handle all of them.

16. **`by-hash` can fail transiently with SSL EOF** — `by-hash` may return `SSL: UNEXPECTED_EOF_WHILE_READING` for a model that does exist. Do NOT conclude the model is missing from a single failed hash lookup. Fallback order: (1) retry `by-hash`, (2) if pretags link already has a model ID, run `model <id>` directly, (3) if `model <id>` is unavailable or stale, re-locate with `models --query`.

17. **Old pretags links can rot** — A stored Civitai URL may parse cleanly but `model <id>` returns HTTP 404. Treat this as a stale registry link, not proof the entry is invalid. Re-search by query/name and update the registry once re-identified.

18. **Downloaded filename may differ from local registry expectation** — The download succeeds but later file checks still report the model missing. Root cause: Civitai's actual published file stem can differ from the `pretags.json` `model file name` already recorded locally. After download, verify the real on-disk filename and align `pretags.json` to the actual stem. Concrete example: model `2039751` publishes `wqmt-gnoob-Tanger.safetensors` but pretags records `无期迷途-noob-Tanger` — later audits produce false "file missing" reports.

## References

- `references/hash-comparison.md` — SHA256 vs AutoV2 format, pretags prefix matching, reproduction of 35-match failure
- `references/model-discovery.md` — finding noob/ill variants, batch checking, tanger patterns, version naming
- `../../tools/pretags-batch-import/SKILL.md` — complete batch import pipeline: discovery → download → tag-split → register → verify
- `../../references/pretags-data-management.md` — LoRA download/registration, batch migration, hash conflict detection
