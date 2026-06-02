# Artstyle Batch Import — Session Notes (2026-05-09)

## Context
Processed ~271 artstyle LoRA files from `$LORA_MODEL_DIR/画风` into `pretags.json` `画风` category. Mixed CivitAI-hit and CivitAI-miss models.

## Key Workflow: CivitAI "Model not found" → Still Add

When by-hash returns `{"error":"Model not found"}`, do NOT skip. User explicitly requires:

```json
{
  "cname": "模型名",
  "Lora": "1",
  "model file name": "stem_no_extension",
  "model hash": "HASH10_HERE",
  "unet weight": "1",
  "clip weight": "1",
  "link": "无",
  "tag": "无",
  "画风描述": ""
}
```

The hash MUST always be filled correctly — it's the deduplication basis.

## Key Workflow: Safetensors Metadata Tag Recovery

When a model has `tag = "无"` or empty, try extracting tags from the safetensors file's embedded metadata:

```python
from safetensors import safe_open
import json

with safe_open(path, framework="numpy") as f:
    meta = f.metadata()

tag_freq_raw = meta.get('ss_tag_frequency', '{}')
tag_freq = json.loads(tag_freq_raw) if isinstance(tag_freq_raw, str) else tag_freq_raw

all_tags = {}
for bucket_name, bucket_tags in tag_freq.items():
    for tag, count in bucket_tags.items():
        all_tags[tag] = all_tags.get(tag, 0) + count

# Filter out generic tags, keep style-specific ones
generic = {'1girl', 'solo', 'looking at viewer', 'breasts', 'long hair', ...}
style_tags = [(t, c) for t, c in sorted(all_tags.items(), key=lambda x: -x[1])
              if t.lower() not in {g.lower() for g in generic} and c >= 2]
top_tags = [t for t, _ in style_tags[:8]]
```

### Key metadata fields in safetensors:
| Field | Meaning |
|-------|---------|
| `ss_tag_frequency` | JSON dict of dataset bucket → {tag: count} — the gold mine for triggers |
| `ss_base_model_version` | Base model (e.g. `sdxl_base_v1-0`) |
| `ss_num_train_images` | Training image count |
| `ss_network_dim` | LoRA dimension |
| `ss_network_alpha` | LoRA alpha |
| `ss_output_name` | Output name |
| `modelspec.title` | Model title |

### Limitations:
- Some models have NO metadata (empty `meta = {}`)
- `NAI_vpred_fix`, stabilizer, detailer models typically have no tags — they're enhancement tools, not style models
- Corrupted files (e.g. truncated download) will throw `MetadataIncompleteBuffer`

## Cron Job vs Manual Batch Processing

| Aspect | Cron Job | Manual Batch |
|--------|----------|-------------|
| Speed per 12 items | 10-20 min | 2-3 min |
| Overhead | Agent startup + API latency each run | Direct Python in terminal |
| Best for | Background trickle, long tail | Rapid bulk processing |

**Lesson**: When user says "快速推进" or "不要停", use manual batch processing. Cron is for "set it and forget it" background tasks.

## Model Re-download Pattern

When a downloaded file is corrupted (e.g. only 3.9MB out of expected 217.9MB):

1. Delete the corrupted file
2. Re-download using `civitai.py download-model MODEL_ID --version-name VERSION -o PATH`
3. Verify: `ls -lh` for size, `hashlib.sha256` for hash match
4. Update `pretags.json` with correct hash and recovered tags from metadata

Example: 无期迷途画风 (model 2039751) — first download got 3.9MB, second got full 218MB with hash `9B29B2FE5F`.
