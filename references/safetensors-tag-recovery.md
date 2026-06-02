# Safetensors 元数据 Tag 提取与清理

当 CivitAI `by-hash` 或 `trainedWords` 无法提供 tag 时，从 `.safetensors` 文件的 `ss_tag_frequency` 元数据中提取训练 tag 作为备选方案。

## 原理

`safetensors` 文件的 metadata 中，`ss_tag_frequency` 字段记录了训练时每个 tag 在各 bucket 中的出现频率。这是模型训练时使用的真实标签数据，可作为触发词/tag 的可靠来源。

```python
from safetensors import safe_open

with safe_open("model.safetensors", framework="numpy") as f:
    meta = f.metadata()
    tag_freq_raw = meta.get("ss_tag_frequency", "{}")
```

`ss_tag_frequency` 结构：
```json
{
  "bucket_001": {"1girl": 100, "solo": 95, "long hair": 80, ...},
  "bucket_002": {"1girl": 50, "standing": 45, ...}
}
```

## 通用提取流程

```python
import json
from safetensors import safe_open

def extract_meta_tags(safetensors_path: str) -> dict:
    """从 safetensors 文件提取训练 tag 频率"""
    with safe_open(safetensors_path, framework="numpy") as f:
        meta = f.metadata()
    
    if not meta:
        return {"status": "no_metadata", "tags": {}}
    
    tag_freq_raw = meta.get("ss_tag_frequency", "{}")
    try:
        tag_freq = json.loads(tag_freq_raw) if isinstance(tag_freq_raw, str) else tag_freq_raw
    except:
        return {"status": "parse_error", "tags": {}}
    
    # 合并所有 bucket 的 tag 频率
    all_tags = {}
    for bucket_name, bucket_tags in tag_freq.items():
        for tag, count in bucket_tags.items():
            all_tags[tag] = all_tags.get(tag, 0) + count
    
    # 附加元信息
    info = {
        "base_model": meta.get("ss_base_model_version", ""),
        "train_images": meta.get("ss_num_train_images", ""),
        "network_dim": meta.get("ss_network_dim", ""),
        "network_alpha": meta.get("ss_network_alpha", ""),
        "output_name": meta.get("ss_output_name", ""),
        "title": meta.get("modelspec.title", ""),
    }
    
    return {"status": "ok", "tags": all_tags, "info": info}
```

## 按模型类型的清理策略

**核心原则：** 不同类型的模型，保留的 tag 完全不同。

### 画风模型（画风分类）

**目标：** 提取画风触发词 / 风格关键词，过滤掉所有通用 booru 标签。

**保留：**
- 训练触发词（如 `shslg`、`hwax`、`lmve`、`oiskl`、`qthb`、`wgcz`）
- 风格关键词（如 `sketch`、`pinup`、`ligne claire`、`line art`、`monochrome`、`greyscale`）
- 领域标签（如 `game cg`、`chinese_clothes`、`chibi`）
- 画师名（如 `artist:chujiujiu`、`booth48`）
- 质量/美学关键词（如 `newest`、`ultra-detailed`、`painting`、`negative space`、`detailed background`）

**过滤（通用 booru 标签）：**
```
人物类：1girl, solo, 1boy, multiple girls, looking at viewer, closed mouth, open mouth, smile
发型类：long hair, short hair, bangs, twintails, braid, black hair, blonde hair, brown hair, white hair, blue hair, pink hair, aqua hair, red hair
眼睛类：blue eyes, red eyes, green eyes, yellow eyes, purple eyes, black eyes
身材类：breasts, large breasts, small breasts, medium breasts, huge breasts, navel, thighs, ass
表情类：blush, parted lips
姿势类：standing, sitting, lying, from side, from above, full body, upper body, portrait, cowboy shot
服装类：shirt, dress, skirt, pants, jacket, long sleeves, gloves, thighhighs, boots, hat, bow, ribbon, necktie, choker, earrings, jewelry, hair ornament, hair flower, collarbone, bare shoulders, underwear, bra
暴露/NSFW类：nipples, pussy, sex, penis, futanari, censored, mosaic censoring, hetero
场景类：white background, simple background, black background, indoors, outdoors, sky, scenery, building, flower, tree
质量类：masterpiece, best quality, highres, absurdres, very awa, very aesthetic, score_9, score_8_up, score_7_up
角色名：hatsune miku, ayanami rei, plana (blue archive), 以及其他具体角色名
画面效果：blurry, blurry_background, depth of field, halftone, sweat
通用动词：holding, holding weapon, weapon, sword, food
```

**示例：**
```python
GENERIC_ARTSTYLE_TAGS = {
    '1girl', 'solo', '1boy', 'multiple girls', 'looking at viewer',
    'closed mouth', 'open mouth', 'smile', 'long hair', 'short hair',
    'bangs', 'twintails', 'braid', 'black hair', 'blonde hair',
    'brown hair', 'white hair', 'blue hair', 'pink hair', 'aqua hair',
    'red hair', 'blue eyes', 'red eyes', 'green eyes', 'yellow eyes',
    'purple eyes', 'black eyes', 'breasts', 'large breasts', 'small breasts',
    'medium breasts', 'huge breasts', 'navel', 'thighs', 'ass', 'blush',
    'parted lips', 'standing', 'sitting', 'from side', 'from above',
    'full body', 'upper body', 'portrait', 'cowboy shot', 'shirt', 'dress',
    'skirt', 'pants', 'jacket', 'long sleeves', 'gloves', 'thighhighs',
    'boots', 'hat', 'bow', 'ribbon', 'necktie', 'choker', 'earrings',
    'jewelry', 'hair ornament', 'hair flower', 'collarbone', 'bare shoulders',
    'underwear', 'bra', 'nipples', 'pussy', 'sex', 'penis', 'futanari',
    'censored', 'mosaic censoring', 'hetero', 'white background',
    'simple background', 'black background', 'indoors', 'outdoors', 'sky',
    'scenery', 'building', 'flower', 'tree', 'masterpiece', 'best quality',
    'highres', 'absurdres', 'very awa', 'very aesthetic', 'score_9',
    'score_8_up', 'score_7_up', 'hatsune miku', 'ayanami rei',
    'plana (blue archive)', 'blurry', 'blurry_background', 'depth of field',
    'halftone', 'sweat', 'holding', 'holding weapon', 'weapon', 'sword', 'food',
    'dress', 'skirt', 'pants', 'jacket',
}

def clean_artstyle_tags(all_tags: dict, min_count: int = 2) -> list:
    """清理画风 tag：过滤通用 booru 标签，保留触发词"""
    style_tags = [
        (t, c) for t, c in sorted(all_tags.items(), key=lambda x: -x[1])
        if t.lower() not in {g.lower() for g in GENERIC_ARTSTYLE_TAGS}
        and c >= min_count
    ]
    return [t for t, _ in style_tags[:8]]
```

### 人物模型（人物分类）

**目标：** 提取角色触发词 + 外貌特征 + 服装特征，严格三类拆分。

**提取逻辑：**
1. 从 `trainedWords` 或高频 tag 中找**角色名/触发词** → 写入 `name`
2. 从高频 tag 中提取**身体特征**（发色、瞳色、发型、体型、种族特征）→ 写入 `外貌`
3. 从高频 tag 中提取**穿着饰品**（衣服、饰品、武器）→ 写入 `服装`

**人物 tag 三类拆分规则：**

| 字段 | 保留的 tag 类型 | 示例 |
|------|----------------|------|
| `name` | 角色触发词（通常来自 trainedWords） | `narmaya_(granblue_fantasy)` |
| `外貌` | 发色、瞳色、发型、体型、种族特征、兽耳/角/尾/翅膀、肤色、纹身 | `1girl, draph, horns, pink_hair, blue_eyes, large_breasts, long_hair` |
| `服装` | 衣服、鞋子、饰品（hair_ornament/tiara/choker/earrings）、武器持有、特殊装扮 | `hair_ornament, black_gloves, white_bikini` |

**外貌 vs 服装判断标准：** 去掉这个 tag 角色仍是"同一个人" → 外貌；去掉后变成"不同装扮" → 服装。

**需过滤的通用 tag（人物模型不需要这些）：**
- 质量标签：`masterpiece, best quality, highres, absurdres`
- 通用数量：`solo, 1girl, 1boy, multiple girls`
- 通用姿势：`standing, sitting, looking at viewer`
- 通用场景：`white background, simple background, indoors, outdoors`

**示例：**
```python
GENERIC_CHARACTER_TAGS = {
    'masterpiece', 'best quality', 'highres', 'absurdres', 'very awa',
    'very aesthetic', 'solo', '1girl', '1boy', 'multiple girls',
    'standing', 'sitting', 'looking at viewer', 'closed mouth', 'open mouth',
    'white background', 'simple background', 'black background',
    'indoors', 'outdoors', 'upper body', 'full body', 'portrait',
}

def clean_character_tags(all_tags: dict, trained_words: list, min_count: int = 2) -> dict:
    """清理人物 tag：提取触发词 + 外貌 + 服装"""
    # 过滤通用标签
    filtered = {
        t: c for t, c in all_tags.items()
        if t.lower() not in {g.lower() for g in GENERIC_CHARACTER_TAGS}
        and c >= min_count
    }
    
    # 外貌关键词
    appearance_kw = {
        'hair', 'eyes', 'skin', 'horns', 'ears', 'tail', 'wings',
        'blonde', 'brunette', 'redhead', 'white hair', 'black hair',
        'blue hair', 'pink hair', 'long hair', 'short hair', 'twintails',
        'braid', 'bangs', 'draph', 'erune', 'human', 'elf', 'fox',
        'cat', 'wolf', 'demon', 'angel', 'large breasts', 'small breasts',
        'petite', 'tall', 'muscular', 'slim', 'voluptuous', 'pale skin',
        'tan', 'tattoo', 'scar', 'freckles', 'fang', 'slit pupils',
    }
    
    # 服装关键词
    clothing_kw = {
        'dress', 'skirt', 'shirt', 'pants', 'bikini', 'swimsuit',
        'armor', 'gloves', 'boots', 'shoes', 'hat', 'crown', 'tiara',
        'choker', 'necklace', 'earrings', 'bracelet', 'ring',
        'hair ornament', 'hair bow', 'ribbon', 'scarf', 'cape',
        'jacket', 'coat', 'hoodie', 'stockings', 'thighhighs',
        'holding', 'weapon', 'sword', 'spear', 'bow', 'staff',
    }
    
    name = []
    appearance = []
    clothing = []
    
    for tag in sorted(filtered, key=lambda t: -filtered[t]):
        tl = tag.lower()
        if any(kw in tl for kw in appearance_kw):
            appearance.append(tag)
        elif any(kw in tl for kw in clothing_kw):
            clothing.append(tag)
    
    return {
        "name": ", ".join(trained_words[:3]) if trained_words else "",
        "外貌": ", ".join(appearance[:10]),
        "服装": ", ".join(clothing[:8]),
    }
```

### 服装模型（服装分类）

**目标：** 提取服装/饰品相关 tag，过滤人物特征和场景标签。

**保留：**
- 服装名称（dress, bikini, armor, school uniform, maid outfit...）
- 饰品（choker, tiara, hair ornament, earrings...）
- 材质（lace, silk, leather, denim...）
- 颜色（black, white, red, blue...）

**过滤：**
- 人物特征（hair color, eye color, body type...）
- 场景（background, indoors, outdoors...）
- 质量标签（masterpiece, best quality...）
- 通用姿势（standing, sitting...）

**示例：**
```python
GENERIC_CLOTHING_TAGS = {
    '1girl', 'solo', '1boy', 'masterpiece', 'best quality', 'highres',
    'absurdres', 'standing', 'sitting', 'looking at viewer',
    'white background', 'simple background', 'black background',
    'indoors', 'outdoors', 'long hair', 'short hair', 'bangs',
    'blue eyes', 'red eyes', 'green eyes', 'black hair', 'blonde hair',
    'breasts', 'large breasts', 'small breasts', 'blush', 'smile',
}

def clean_clothing_tags(all_tags: dict, min_count: int = 2) -> list:
    """清理服装 tag：保留服装/饰品/材质相关"""
    clothing_tags = [
        (t, c) for t, c in sorted(all_tags.items(), key=lambda x: -x[1])
        if t.lower() not in {g.lower() for g in GENERIC_CLOTHING_TAGS}
        and c >= min_count
    ]
    return [t for t, _ in clothing_tags[:10]]
```

### 其他模型（动作/镜头/场景/其他）

这些分类通常不含 LoRA（`Lora=0`），不需要 tag 提取。如果遇到含 LoRA 的条目：

- **动作**：保留姿势/动作相关 tag，过滤人物/场景
- **镜头**：保留视角/构图 tag
- **场景**：保留环境/背景 tag，过滤人物特征
- **其他**：按具体内容判断

## 不可提取的模型类型

以下类型的 `.safetensors` 文件通常**没有训练 tag**（`ss_tag_frequency` 为空或极简）：

| 类型 | 特征 | 处理 |
|------|------|------|
| **Stabilizer** | 文件名含 `stabilizer`，dim ≤ 8 | tag 填"无"，画风描述写"稳定器/增强类" |
| **Detailer** | 文件名含 `detailer` | tag 填"无"，画风描述写"细节增强类" |
| **Merged** | `ss_training_comment` 含 `lora_merged` | tag 填"无" |
| **Extracted** | dim=0/0，无训练元信息 | tag 填"无" |
| **无 metadata** | `f.metadata()` 返回 None | tag 填"无"，需从文件名/来源推断 |

## 完整提取 + 清理工作流

```python
import json, os
from safetensors import safe_open

def extract_and_clean(safetensors_path: str, model_type: str, trained_words: list = None) -> dict:
    """
    从 safetensors 文件提取并清理 tag。
    
    model_type: 'artstyle' | 'character' | 'clothing' | 'action' | 'scene' | 'other'
    """
    result = extract_meta_tags(safetensors_path)
    
    if result["status"] != "ok":
        return {"tag": "无", "status": result["status"]}
    
    all_tags = result["tags"]
    if not all_tags:
        return {"tag": "无", "status": "no_tags", "info": result["info"]}
    
    if model_type == "artstyle":
        cleaned = clean_artstyle_tags(all_tags)
        return {"tag": ", ".join(cleaned) if cleaned else "无", "status": "ok", "info": result["info"]}
    
    elif model_type == "character":
        cleaned = clean_character_tags(all_tags, trained_words or [])
        return {**cleaned, "status": "ok", "info": result["info"]}
    
    elif model_type == "clothing":
        cleaned = clean_clothing_tags(all_tags)
        return {"tag": ", ".join(cleaned) if cleaned else "无", "status": "ok", "info": result["info"]}
    
    else:
        # 通用：过滤质量标签后取 top 8
        quality_tags = {'masterpiece', 'best quality', 'highres', 'absurdres', 
                       'very awa', 'very aesthetic', 'score_9', 'score_8_up', 'score_7_up',
                       '1girl', 'solo', '1boy'}
        filtered = [(t, c) for t, c in sorted(all_tags.items(), key=lambda x: -x[1])
                    if t.lower() not in {g.lower() for g in quality_tags} and c >= 2]
        cleaned = [t for t, _ in filtered[:8]]
        return {"tag": ", ".join(cleaned) if cleaned else "无", "status": "ok", "info": result["info"]}
```

## 使用场景

### 场景 1：批量补全缺 tag 的画风条目

```python
import json, os
from safetensors import safe_open

pretags_path = 'assets/pretags.json'
artdir = '/opt/comfyui/save/models/loras/画风'

with open(pretags_path, 'r') as f:
    data = json.load(f)

no_tag = []
for k, v in data['画风'].items():
    if isinstance(v, dict) and (not v.get('tag') or v.get('tag') in ('', '无')):
        mf = v.get('model file name', '')
        path = os.path.join(artdir, mf + '.safetensors')
        if os.path.exists(path):
            no_tag.append((k, mf, path))

for cname, mf, path in no_tag:
    result = extract_and_clean(path, 'artstyle')
    if result['tag'] != '无':
        data['画风'][cname]['tag'] = result['tag']

with open(pretags_path, 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 场景 2：新模型入库时自动提取 tag

入库新画风 LoRA 时，如果 CivitAI 无 tag，自动从 meta 提取：

```python
# 入库流程
hash10 = compute_hash(path)
civitai_info = query_civitai_by_hash(hash10)

if civitai_info and civitai_info.get('trainedWords'):
    tag = ", ".join(civitai_info['trainedWords'][:5])
else:
    # Fallback: 从 meta 提取
    result = extract_and_clean(path, 'artstyle')
    tag = result['tag']

entry = {
    "cname": stem,
    "Lora": "1",
    "model file name": stem,
    "model hash": hash10,
    "unet weight": "1",
    "clip weight": "1",
    "link": f"https://civitai.com/models/{civitai_info['modelId']}" if civitai_info else "无",
    "tag": tag,
    "画风描述": "待补充",
}
```

## 注意事项

1. **safetensors 库依赖**：需要 `pip install safetensors`
2. **大文件读取**：`safe_open` 只读取 metadata，不加载权重，速度快
3. **tag 大小写**：`ss_tag_frequency` 中的 tag 大小写不统一，清理时需 `lower()` 比较
4. **频率阈值**：建议 `min_count >= 2`，过滤掉只出现一次的噪声 tag
5. **最大 tag 数**：画风取 top 8，人物取 top 10 外貌 + top 8 服装
6. **中文 tag**：`ss_tag_frequency` 中偶尔有中文 tag（如训练数据包含中文标注），需额外翻译
