# Model Discovery Patterns

## tanger Creator Patterns

### Model naming conventions
- Individual character: `【Game】Character Name (SDXL | Pony | Noob | Artiwaifu | SD15)`
- Multi-character: `【Game】Character A & Character B`
- Clothing: `[Character | Clothes]【Game】Character - Outfit`
- Style: `【style】【Game】` or `Some NSFW Style for ...`

### Base model variants (per model)
Every tanger model typically has multiple versions:
- `noob` — NoobAI-XL (SDXL-based)
- `pony` — Pony Diffusion V6 XL
- `ill` / `will` / `illustrious` — Illustrious-XL (**note**: version name varies)
- `A3` — Animagine XL V3
- `Artiwaifu` / `atw` — ArtiWaifu Diffusion
- `SD15` — SD 1.5
- `kohaku` — Kohaku (less common)

### Illustrious version naming (CRITICAL)
tanger does NOT use `"ill"` as version name for Illustrious. Uses:
- `"will"` — most common
- `"illustrious"` — some models
- `"ill"` — rare

**Always inspect first:**
```bash
python civitai.py model <id> | python3 -c "
import json,sys; d=json.load(sys.stdin)
[print(f'v{v[\"id\"]} name=\"{v[\"name\"]}\" base={v[\"baseModel\"]}') 
 for v in d.get('modelVersions',[])]"
```

### Family bundle (ID: 851411)
`(SDXL: NoobAI) MIHOYO Collection 米家全家桶` contains 36 versions covering ALL characters. Individual character models often have DIFFERENT file hashes than the bundle version (e.g., feixiao `000007` vs bundle `000014`).

### New model patterns
- Recent models (IDs > 2000000) have both noob + Illustrious for EVERY character
- Ill-only models: some non-mainstream IPs (和平精英, 崩坏学园2, 阴阳师) only get Illustrious versions
- Model titles may omit "Noob" but the file STILL has noob version

## Discovery Workflow

### Quick scan for noob/ill
```bash
for mid in <new_ids>; do
  result=$(python civitai.py --host civitai.red model $mid 2>&1)
  n=$(echo "$result" | python3 -c "
    import json,sys; d=json.load(sys.stdin)
    vs=d.get('modelVersions',[])
    print(sum(1 for v in vs if 'noob' in (v.get('baseModel','')+v.get('name','')).lower()))
  " 2>/dev/null)
  i=$(echo "$result" | python3 -c "
    import json,sys; d=json.load(sys.stdin)
    vs=d.get('modelVersions',[])
    print(sum(1 for v in vs if 'ill' in (v.get('baseModel','')+v.get('name','')).lower()))
  " 2>/dev/null)
  [ "$n" != "0" ] || [ "$i" != "0" ] && echo "🆕 ID:$mid noob=$n ill=$i"
done
```

### Batch hash comparison
After discovering models with noob/ill:
1. Get their file hashes via `model <id>`
2. Compare against pretags with **prefix matching** (see `hash-comparison.md`)
3. Download only truly missing files
