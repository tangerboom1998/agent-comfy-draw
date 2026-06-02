# 画风管理与测试工作流

> 合并自: artstyle-curation-workflow.md, artstyle-description-cleanup.md, artstyle-testing-workflow.md, batch-artstyle-testing.md, artstyle_descriptions.md

---

## 一、画风 LoRA 整理流程

### Step 1 — 全局摸底

扫描画风 LoRA 目录，统计文件和 pretags 条目：

```bash
# 统计磁盘文件
ls loras/画风/ | wc -l
# 统计 pretags 条目
python -c "import json; d=json.load(open('pretags.json')); print(len(d['画风']))"
```

### Step 2 — Hash 去重

按文件 hash 分组，检测重复文件：

```python
import hashlib, os
from collections import defaultdict

LORA_DIR = os.environ.get('LORA_MODEL_DIR', '') + '/画风/'
hashes = defaultdict(list)
for f in os.listdir(LORA_DIR):
    if f.endswith('.safetensors'):
        path = os.path.join(LORA_DIR, f)
        h = hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]
        hashes[h].append(f)

for h, files in hashes.items():
    if len(files) > 1:
        print(f"Duplicate hash {h}: {files}")
```

### Step 3 — 补充 Civitai 信息

通过 civitai-api 获取：
- `modelId`（Civitai 模型 ID）
- `activation text`（触发词）
- 基础描述

```bash
# 已知 modelId 时直接查
lark-cli civitai-api +get-model --model-id 12345
```

### Step 3.5 — 从 safetensors 元数据提取 tag（备选方案）

当 Civitai API 无法获取时，从 safetensors 文件头提取训练 tag（详见 `safetensors-tag-recovery.md`）。

### Step 4 — 补充画风描述

通过 artstyle-test 工具逐批测试：

```bash
# 单张测试
python tools/artstyle-test/artstyle_test.py --cname "wlop" --steps 20 --cfg 5

# 批量模式
python tools/artstyle-test/artstyle_test.py --batch --limit 10
```

### Step 5 — 处理磁盘未入库文件

```bash
# 列出磁盘有但 pretags 没有的文件
python tools/pretags-batch-import/scan_missing.py --model-type 画风
```

---

## 二、画风测试工作流

### 测试维度

每个画风需要测试 3 个维度：

1. **只有角色**（无场景）— 看画风对人像的处理
2. **只有场景**（无角色）— 看画风对背景的处理
3. **角色+场景** — 综合评估

### 测试 Prompt 模板

```
masterpiece, best quality, safe, @{artstyle_cname},
1girl, solo, silver hair, long hair, red eyes,
white dress, standing, looking at viewer,
castle background, moonlight,
```

### 批量测试流水线

每批 10 个画风，3-4 分钟/批：

1. 从 pretags 选取 Lora=1 且 tag 非空的画风
2. 自动选取前 5 个进行测试
3. 每个画风生成 3 张（对应 3 个测试维度）
4. 用 vision_analyze 分析结果

```bash
# 自动选取前5个有LoRA且tag非空的画风
python tools/artstyle-test/artstyle_test.py --auto --count 5

# 指定数量
python tools/artstyle-test/artstyle_test.py --auto --count 10
```

### vision_analyze 子 agent 提示词模板

```
分析这张图的艺术风格特征，重点描述：
1. 笔触风格（厚涂/水彩/线稿/CG等）
2. 配色倾向（暖/冷/饱和/灰调）
3. 光影处理（柔和/硬朗/戏剧光/平光）
4. 线条风格（粗/细/无描边/有描边）
5. 整体质感（光滑/粗糙/油画感/数码感）

用中文简短描述（50字以内），避免评价性语言，只描述客观特征。
```

---

## 三、画风描述规范（强制）

### 标准描述格式

```
[笔触风格]，[配色倾向]，[光影特征]，[线条风格]，[整体质感]
```

### 已测试画风描述汇总

| 画风 | 描述 |
|------|------|
| `wlop` | 唯美幻想，厚涂光影，柔和朦胧光，冷紫蓝调，数码厚涂 |
| `ask` | 精美日系，柔和配色，明亮自然光，细线描边，CG质感 |
| `fu_mi` | 性感厚涂，温暖色调，柔光，无描边，油画感 |
| `reoenl` | 韩系半写实，柔和色彩，自然光，细线描边，插画风格 |
| `sciamano240` | 极致精细，高饱和度，戏剧光，无描边，超高清CG |
| `sakimichan` | 唯美厚涂，高饱和，柔和光，无描边，CG厚涂 |
| `hiten` | 纯爱唯美，柔和色彩，自然光，细线描边，清新CG |
| `greem_bang` | 韩系纯爱，温暖色调，柔和光，细线描边，插画风格 |
| `cacao` | 油画厚涂，暖色调，暗光，粗笔触，油画质感 |
| `lack` | 清冷高级，低饱和，硬朗光，清晰描边，平面CG |
| `mochi_icecream` | Q版可爱，明亮配色，平光，粗线描边，卡通风格 |
| `kedama_milk` | Q版幼态，柔和色彩，平光，粗描边，可爱卡通 |
| `wanke` | 唯美日系，亮色配比，自然光，细描边，CG插画 |
| `ka_ya` | 韩系唯美，温暖色调，柔和光，无描边，厚涂 |
| `limgae` | 韩系厚涂，高饱和，戏剧光，无描边，CG厚涂 |
| `nixeu` | 唯美插画，冷色调，柔和光，细描边，CG质感 |
| `shal_e` | 厚涂，温暖色调，柔和光，粗笔触，油画质感 |
| `anmi` | 日系清新，柔和色彩，自然光，细描边，水彩感 |
| `chen_bin` | 中国风厚涂，浓郁色彩，戏剧光，粗笔触，油画质感 |
| `axel_medellin` | 美漫风格，高饱和，硬朗光，粗描边，美漫质感 |
| `james_jean` | 超现实，柔和色彩，梦幻光，细描边，插画风格 |
| `loish` | 唯美插画，柔和色彩，自然光，细描边，水彩感 |
| `rossdraws` | 唯美CG，高饱和，柔和光，细描边，CG质感 |
| `artgerm` | 美漫CG，高饱和，硬朗光，粗描边，CG质感 |
| `guweiz` | 日系写实，冷色调，自然光，细描边，插画风格 |
| `ilya_kuvshinov` | 唯美日系，柔和色彩，自然光，细描边，水彩 |

---

## 四、非标准画风描述检测与清理

### 检测规则（19 种模式，2026-05 实测 150 条命中）

| 规则 | 模式 | 示例 |
|------|------|------|
| 1 | 只有"高品质"等模糊描述 | `高品质` |
| 2 | 英文+中文混合 | `anime style 高品质` |
| 3 | 纯触发词 | `solo_lee style` |
| 4 | 文件路径式 | `/path/to/lora` |
| 5 | 只有"xxx风格" | `日系风格` |
| 6 | 空或仅空白 | ` ` |
| 7 | 单字 | `厚涂` |
| 8 | 负面描述 | `不太清晰` |
| 9 | 主观评价 | `很好看` |
| 10 | 纯数字/ID | `12345` |
| 11 | 问号/未知 | `???` `unknown` |
| 12 | 过度简洁（<5字） | — |
| 13 | 非描述性文本 | `暂无` `待补充` |
| 14 | 纯标点 | `---` |
| 15 | 包含 URL | `https://...` |
| 16 | 纯英文+无结构 | `beautiful style` |
| 17 | 角色名而非画风 | `saber`, `rem` |
| 18 | 技术参数 | `cfg=7, steps=30` |
| 19 | 中文口语 | `这个画风挺好看的` |

### 扫描脚本

```python
import json, re

with open('pretags.json') as f:
    data = json.load(f)

nonstandard = []
for cname, info in data['画风'].items():
    desc = info.get('description', '').strip()
    if not desc or len(desc) < 5:
        nonstandard.append((cname, desc, 'empty_or_too_short'))
    # ... 其他规则

print(f"共发现 {len(nonstandard)} 条非标准描述")
```

### ⚠️ "高品质" 误伤风险

部分条目描述中包含 `高品质` 但后续有有效描述，如 `高品质，厚涂，暖色调`。这类不应清空——只检测 **仅含模糊词** 的条目。

### 批量清空脚本

```python
# 只清空完全命中非标准规则的条目
for cname, desc, rule in nonstandard:
    data['画风'][cname]['description'] = ''
```

---

## 五、性能参考

| 操作 | 耗时 |
|------|------|
| 批量测试 10 个画风（各3维度） | ~30-40 分钟 |
| vision_analyze 单张 | ~15-30 秒 |
| Hash 扫描 200+ 文件 | <5 秒 |
| Civitai API 单次查询 | ~2-5 秒 |

---

## 注意事项

1. **artstyle_test.py 批量模式**不稳定时建议逐个处理
2. **Hash 格式**：统一使用 sha256 前 16 位
3. **画风描述字段类型**：纯文本中文描述，50 字以内
4. **safetensors 元数据 tag**：需要专门清理（见 safetensors-tag-recovery.md）
5. **LoRA 调用格式**：使用 `lora_file` 字段中的文件名（不带路径前缀）
