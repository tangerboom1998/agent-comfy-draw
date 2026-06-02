---
name: danbooru-tag-scraper
description: "Danbooru 精细化标签爬取：通过代理访问 Danbooru API，按类别（发色/瞳色/服装/表情/姿势/背景…）批量爬取标签，构建 AI 绘图 prompt 标签词典。支持标签搜索、关联标签发现、帖子标签提取。"
metadata: {"openclaw": {"emoji": "🏷️", "requires": {"env": []}}}
---

# Danbooru 精细化标签爬取

> 通过代理访问 Danbooru API，爬取、搜索、归类、关联动漫风格图像的精细化标签。
> 适用于 AI 绘图 prompt 工程、标签词典构建、图像数据集标注参考。

## 触发条件

- 用户要求从 Danbooru 搜标签、爬标签、获取标签列表
- 用户需要特定类别（发色/瞳色/服装/表情/姿势…）的标签集合
- 用户想了解某个标签的关联标签、wiki 说明
- 用户需要从帖子提取标签用于 prompt 构造

## 环境

### 代理配置（必须）

Danbooru 需通过代理访问。本 skill 所有网络请求**必须**走代理：

```python
import os
PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('ALL_PROXY') or 'http://127.0.0.1:7890'
```

**重要**：terminal 工具 curl 可能因安全策略拦截代理连接，**始终使用 execute_code（Python urllib）**发起请求。

### 速率控制

Danbooru 无硬性 rate-limit header，但应保持礼貌：
- 连续请求间隔 ≥ 1 秒
- 批量爬取时每 10 个请求 sleep 2 秒
- 单次脚本不超过 100 个请求

## API 参考

### 核心端点

| 端点 | 用途 | 关键参数 |
|------|------|----------|
| `/tags.json` | 搜索/列出标签 | `search[name_matches]`, `search[category]`, `search[order]`, `limit`, `page` |
| `/related_tag.json` | 查询关联标签 | `query` (标签名), `category` (限制类别) |
| `/tag_aliases.json` | 标签别名 | `search[name_matches]`, `search[antecedent_name]` |
| `/wiki_pages/<tag>.json` | 标签 wiki | 路径参数为标签名 |
| `/autocomplete.json` | 标签自动补全 | `search[query]`, `search[type]=tag_query` |
| `/posts.json` | 搜索帖子 | `tags` (空格分隔), `limit`, `page` |
| `/posts/<id>.json` | 帖子详情+标签 | 路径参数为帖子 ID |
| `/explore/posts/popular.json` | 热门帖子 | — |

### 标签类别 (category)

| 值 | 含义 | 示例 |
|----|------|------|
| `0` | general | 1girl, dress, blue_eyes, smile, standing |
| `1` | artist | kyogoku_shin, wlop |
| `3` | copyright | genshin_impact, blue_archive, original |
| `4` | character | hatsune_miku, hu_tao_(genshin_impact) |
| `5` | meta | highres, bad_id, commentary |

### `tags.json` 搜索参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `search[name_matches]` | 通配符匹配标签名 | `*dress*`, `blue_*` |
| `search[category]` | 按类别过滤 | `0`, `4` |
| `search[order]` | 排序 | `count` (帖子数), `date` (创建时间), `name` |
| `search[hide_empty]` | 隐藏零帖子标签 | `true` |
| `search[is_deprecated]` | 仅废弃标签 | `true` |

### 帖子搜索语法

`tags` 参数支持空格分隔的复合查询：

| 语法 | 含义 |
|------|------|
| `tag1 tag2` | AND（同时包含） |
| `~tag1 ~tag2` | OR（任一包含） |
| `-tag1` | NOT（排除） |
| `tag1 score:>100` | 评分过滤 |

## 工作流

### 工作流 1：按通配符批量爬标签

获取某一类标签的完整列表（如所有发色标签）。

```python
import urllib.request
import json
import time

PROXY = os.environ.get('HTTPS_PROXY') or os.environ.get('ALL_PROXY') or 'http://127.0.0.1:7890'
proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)

def fetch_all_tags(pattern, category=None, min_posts=100):
    """爬取匹配 pattern 的全部标签"""
    all_tags = []
    page = 1

    while True:
        params = f'search[name_matches]={urllib.request.quote(pattern)}&search[order]=count&limit=100&page={page}'
        if category is not None:
            params += f'&search[category]={category}'

        url = f'https://danbooru.donmai.us/tags.json?{params}'
        resp = opener.open(url, timeout=15)
        data = json.loads(resp.read())

        if not data:
            break

        for t in data:
            if t['post_count'] >= min_posts and not t.get('is_deprecated', False):
                all_tags.append(t)

        if len(data) < 100:
            break

        page += 1
        time.sleep(1)

    return all_tags

# 示例：获取所有发色标签（min_posts >= 500）
# tags = fetch_all_tags('*_hair', category=0, min_posts=500)
# for t in sorted(tags, key=lambda x: -x['post_count']):
#     print(f"{t['name']}: {t['post_count']}")
```

### 工作流 2：按帖子提取标签集

给定搜索条件，从帖子中提取并统计标签频次。

```python
from collections import Counter

def extract_tags_from_posts(tag_query, max_posts=100):
    """从匹配帖子中提取所有标签并统计频次"""
    tag_counter = Counter()
    page = 1
    collected = 0

    while collected < max_posts:
        url = f'https://danbooru.donmai.us/posts.json?tags={urllib.request.quote(tag_query)}&limit=100&page={page}'
        resp = opener.open(url, timeout=15)
        posts = json.loads(resp.read())

        if not posts:
            break

        for post in posts:
            tags = post.get('tag_string', '').split()
            tag_counter.update(tags)

        collected += len(posts)
        if len(posts) < 100:
            break
        page += 1
        time.sleep(1)

    return tag_counter

# 示例：提取 blue_archive 相关帖子的高频标签
# counter = extract_tags_from_posts('blue_archive', max_posts=200)
# for tag, count in counter.most_common(50):
#     print(f"{tag}: {count}")
```

### 工作流 3：获取关联标签

发现与某标签高度共现的其他标签，构建 prompt 组合。

```python
def get_related_tags(tag, category='general'):
    """获取指定标签的关联标签"""
    url = f'https://danbooru.donmai.us/related_tag.json?query={urllib.request.quote(tag)}&category={category}'
    resp = opener.open(url, timeout=15)
    return json.loads(resp.read())
```

### 工作流 4：构建分类标签词典

按类别爬取完整的精细化标签集，输出 JSON 词典。

```python
def build_tag_dict(output_path='danbooru_tags.json'):
    """构建分类型的标签词典"""
    categories = {
        'hair_color': '*_hair',
        'eye_color': '*_eyes',
        'hairstyle': '*_ponytail OR *_bangs OR *_braid OR *_bun OR *_twintails OR *_bob',
        'clothing_dress': '*_dress',
        'clothing_upper': '*_shirt OR *_jacket OR *_sweater OR *_hoodie OR *_blouse OR *_vest',
        'clothing_lower': '*_skirt OR *_pants OR *_shorts',
        'clothing_footwear': '*_shoes OR *_boots OR *_socks OR *_thighhighs OR *_stockings',
        'expression': '*_expression OR *smile* OR *blush* OR *frown* OR *angry* OR *cry* OR *laugh*',
        'pose': '*standing* OR *sitting* OR *lying* OR *_pose OR *arms_up* OR *hand*',
        'accessories': '*_ribbon OR *_bow OR *_hat OR *_glasses OR *_necklace OR *_earrings',
        'background': '*_background OR *_sky OR *outdoor* OR *indoor* OR *_room OR *_scenery',
        'viewpoint': '*cowboy_shot* OR *close-up* OR *full_body* OR *from_above* OR *from_below*',
    }

    result = {}
    for cat_name, pattern in categories.items():
        tags = fetch_all_tags(pattern, category=0, min_posts=200)
        result[cat_name] = [{'name': t['name'], 'count': t['post_count']} for t in tags]
        print(f"[{cat_name}] fetched {len(tags)} tags")
        time.sleep(2)

    with open(output_path, 'w') as f:
        json.dump({'_meta': {'source': 'danbooru.donmai.us',
                              'fetched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
                    **result}, f, ensure_ascii=False, indent=2)
    return result
```

### 工作流 5：标签详情查询

获取标签的 wiki 说明、别名。

```python
def get_tag_info(tag_name):
    """获取标签完整信息"""
    info = {}

    # Wiki
    try:
        resp = opener.open(f'https://danbooru.donmai.us/wiki_pages/{urllib.request.quote(tag_name)}.json', timeout=10)
        wiki = json.loads(resp.read())
        info['wiki'] = wiki.get('body', '')
    except:
        info['wiki'] = None

    # Aliases
    try:
        resp = opener.open(f'https://danbooru.donmai.us/tag_aliases.json?search[consequent_name]={urllib.request.quote(tag_name)}&limit=20', timeout=10)
        info['aliases_from'] = [a['antecedent_name'] for a in json.loads(resp.read())]
    except:
        info['aliases_from'] = []

    return info
```

### 工作流 6：角色标签三步法

> **核心思路**：Danbooru 闭环即可获得角色的正确英文名和 Source 归属，不需要外部搜索引擎。
> 角色标签 wiki 正文里就写了英文名、声优、系列出处。

**三步流程**：

```
① 定系列 → ② 提角色 → ③ 补wiki信息
```

#### Step 1 — 爬取系列列表

获取 category=3 (copyright) 的 Top N 热门系列：

```python
def get_top_series(n=50, min_posts=1000):
    """获取热门系列列表"""
    series = []
    page = 1
    while len(series) < n:
        url = f'https://danbooru.donmai.us/tags.json?search[category]=3&search[order]=count&search[hide_empty]=true&limit=100&page={page}'
        resp = opener.open(url, timeout=15)
        data = json.loads(resp.read())
        if not data:
            break
        for t in data:
            if t['post_count'] >= min_posts and not t.get('is_deprecated'):
                series.append({'name': t['name'], 'posts': t['post_count']})
                if len(series) >= n:
                    break
        page += 1
        time.sleep(1)
    return series
```

#### Step 2 — 提取角色（两条路互补）

**路线 A：帖子提取**（推荐，覆盖全）
从系列帖子的 `tag_string_character` 字段提取角色：

```python
def extract_characters_from_series(series_tag, max_posts=300):
    """从系列帖子中提取角色标签"""
    from collections import Counter
    char_counter = Counter()
    collected = 0
    page = 1

    while collected < max_posts:
        url = f'https://danbooru.donmai.us/posts.json?tags={urllib.request.quote(series_tag)}&limit=100&page={page}'
        resp = opener.open(url, timeout=15)
        posts = json.loads(resp.read())
        if not posts:
            break
        for p in posts:
            chars = p.get('tag_string_character', '').split()
            char_counter.update(chars)
        collected += len(posts)
        if len(posts) < 100:
            break
        page += 1
        time.sleep(1)

    return char_counter
```

**路线 B：通配符搜索**（补充遗漏）
搜 `*(series_suffix)` 直接命中带系列后缀的角色标签：

```python
def search_characters_by_suffix(suffix, min_posts=5):
    """搜索 *(suffix) 格式的角色标签"""
    # suffix 如: re:zero, genshin_impact, blue_archive
    url = f'https://danbooru.donmai.us/tags.json?search[name_matches]=*({urllib.request.quote(suffix)})&search[category]=4&search[order]=count&search[hide_empty]=true&limit=200'
    resp = opener.open(url, timeout=15)
    data = json.loads(resp.read())
    return [t for t in data if t['post_count'] >= min_posts and not t.get('is_deprecated')]
```

**注意**：
- 路线 A 能发现不带系列后缀的角色（如部分角色直接 `character_name` 无括号），也能捡到跨系列 tag
- 路线 B 更精确，仅命中标准 `角色_(系列)` 格式
- 两条路的结果合并去重，以频次高的为准

#### Step 3 — 补充 wiki 信息

每个角色调 wiki 获取英文名和描述：

```python
def get_character_info(tag_name):
    """从 wiki 提取角色信息"""
    info = {'tag': tag_name, 'english_name': None, 'source': None, 'description': None, 'appearance_tags': []}

    try:
        resp = opener.open(f'https://danbooru.donmai.us/wiki_pages/{urllib.request.quote(tag_name)}.json', timeout=10)
        wiki = json.loads(resp.read())
        body = wiki.get('body', '') or ''
        info['description'] = body

        # wiki 首句通常是 "A character from [Series Name]"
        if 'character from' in body.lower():
            info['source'] = body.split('character from')[1].split('.')[0].strip().strip('[]').replace('[[', '').replace(']]', '')

        # 英文名 = 括号前部分，首字母大写
        base_name = tag_name.split('(')[0].replace('_', ' ').title()
        info['english_name'] = base_name

    except:
        pass

    return info
```

#### 完整流程

```python
def build_character_dict(top_n_series=30, posts_per_series=300):
    """构建 {系列: [角色列表]} 词典"""
    result = {}

    # Step 1
    series_list = get_top_series(n=top_n_series, min_posts=1000)
    print(f"Step 1: Got {len(series_list)} series")

    for s in series_list:
        series_name = s['name']
        print(f"\n--- {series_name} ---")

        # Step 2A: 帖子提取
        chars = extract_characters_from_series(series_name, max_posts=posts_per_series)
        print(f"  Posts: {len(chars)} characters found")

        # Step 2B: 通配符搜索（补充）
        suffix_chars = search_characters_by_suffix(series_name, min_posts=5)
        for c in suffix_chars:
            if c['name'] not in chars:
                chars[c['name']] = c['post_count']
        print(f"  After suffix merge: {len(chars)} characters")

        # 仅保留 post_count >= 3 的角色
        chars = {k: v for k, v in chars.items() if v >= 3}

        # Step 3: 补 wiki（采样前 20 个高频角色）
        top_chars = sorted(chars.items(), key=lambda x: -x[1])[:20]
        char_entries = []
        for tag_name, count in top_chars:
            info = get_character_info(tag_name)
            info['post_count'] = count
            char_entries.append(info)
            time.sleep(0.5)

        result[series_name] = char_entries
        time.sleep(1)

    return result
```

#### 标签分类与去噪

从 `tag_string_general` 提取标签后，**必须**将标签分为「外貌」「服装」两类，并剔除与人物特征无关的标签。

**分类策略：两阶段**——

| 阶段 | 方法 | 说明 |
|------|------|------|
| **第一阶段：剔除** | 硬编码通配符 | 确定性高的非人物特征标签，直接过滤 |
| **第二阶段：分类** | **Agent 智能判断** | 剩余标签由 agent 逐条判断属于外貌还是服装 |

> **为什么第二阶段用 agent 而非穷举模式匹配**：Danbooru 标签高度规律但**不绝对规律**。新标签、角色特有外貌特征（如 `oni_horns`、`floating_hair`）、文化限定服装名等无法穷举。agent 根据标签语义做判断，配合少量模式辅助，覆盖率和准确率远超硬编码。

---

**第一阶段：强制剔除列表**（硬编码，确定性高）

这些标签与人物外在特征无关，直接过滤：

```python
EXCLUDE_PATTERNS = [
    # 构图 / 场景
    'solo', 'looking_at_viewer', '*_background', 'simple_background',
    'white_background', 'gradient_background',
    # 姿势 / 动作
    'standing', 'sitting', 'lying', 'kneeling', 'squatting',
    'arms_up', 'hands_up', '*hand_on_*', 'arms_behind_back', 'crossed_arms',
    # 视角
    'from_above', 'from_below', 'cowboy_shot', 'close-up', 'full_body',
    'wide_shot', 'dutch_angle', 'head_out_of_frame', 'profile',
    # 表情（通用类，非角色特有）
    'smile', ':d', ':o', ':3', ':q', ':p',
    # 画质 / 元数据
    'absurdres', 'highres', 'monochrome', 'greyscale', 'sketch',
    'watermark', 'signature', 'signed', 'commentary_request', 'bad_id',
    'translated', 'official_art', 'cover', 'artist_name',
    # 武器 / 手持物（非角色固有外观）
    'weapon', '*_holding', 'holding_*', 'holding',
    # 光影 / 特效
    '*_focus', 'light_particles', '*_lighting', '*_light',
    # 计数标签
    '1girl', '1boy', '1other', 'multiple_girls', 'multiple_boys',
]
```

**剔除函数**（仅做第一阶段过滤）：

```python
import fnmatch

def filter_excluded(tag_counts):
    """硬编码剔除，返回 remaining 和 excluded"""
    remaining = {}
    excluded = {}
    for tag, count in tag_counts.items():
        if any(fnmatch.fnmatch(tag, pat) for pat in EXCLUDE_PATTERNS):
            excluded[tag] = count
        else:
            remaining[tag] = count
    return remaining, excluded
```

---

**第二阶段：Agent 分类（智能判断）**

剔除后的剩余标签，**由 agent 逐条判断归属**。分类原则：

| 类别 | 判定标准 | 示例 |
|------|---------|------|
| **外貌** | 人物的**固有生理特征**——发色、瞳色、发型、面部特征、体型、肤色、种族特征（耳/角/尾/翼/牙/肤质）、体态、身高、年龄感 | `brown_hair`, `red_eyes`, `twin_braids`, `blush`, `animal_ears`, `horns`, `ahoge`, `fangs`, `small_breasts`, `dark_skin`, `mole`, `freckles`, `oni_horns`, `elf_ears`, `floating_hair`, `very_long_hair` |
| **服装** | 人物**穿戴在身上的物品**——衣物、鞋袜、帽子、眼镜、首饰、围巾、手套、面具、绷带、包袋、任何可脱卸的饰品和装束 | `kimono`, `thighhighs`, `boots`, `hair_ribbon`, `glasses`, `choker`, `cape`, `armor`, `bandages`, `backpack`, `mask`, `veil`, `crown`, `earrings` |

**判断铁律**：

1. **"能脱下来的就是服装"**——这是最高优先级判定规则。帽子、眼镜、首饰、围巾、面具、绷带、假肢装甲等一切可穿戴/可摘卸物品，归服装。
2. **"长在身上的就是外貌"**——角、翅膀、尾巴、耳朵（兽耳/精灵耳）、獠牙、肤色、瞳色、发色、体型，归外貌。
3. **角色特有外貌特征**按语义判断——如 `oni_horns`（鬼角）是外貌，`oni_mask`（鬼面具）是服装。
4. **`blush` / `tears` / `sweat`** 等表情/生理反应归外貌。
5. **毛发相关**：`*_hair`、`*_ponytail`、`*_bangs` 等归外貌；但 `hair_ribbon`、`hair_ornament`、`hairpin`、`hairclip`、`hairflower` 是可摘卸饰品，归服装。
6. **`barefoot`** 是"没穿鞋"的状态，非穿戴物，归外貌。
7. **不确定时**：查 Danbooru wiki（`/wiki_pages/<tag>.json`），根据描述判断。

**分类流程**：

```
标签列表 → 第一阶段过滤(剔除列表) → 剩余标签 → Agent 逐条判断 → {外貌, 服装}
```

**Agent 执行时**：
- 对剩余标签按覆盖率排序，逐个输出判断和理由
- 每批 ≤ 30 个标签，避免上下文膨胀
- 最终汇总为 `appearance_tags` 和 `clothing_tags` 两个列表

---

**格式化输出函数**（分类结果 → 三区 tag 串）：

```python
def format_character_tagline(character_tag, appearance_tags, clothing_tags, tag_counts, threshold=0.15):
    """将 agent 分类后的结果格式化为三区 tag 串"""
    def filter_by_coverage(tags, counts, threshold):
        if not tags:
            return []
        total = sum(counts.get(t, 0) for t in tags)
        if not total:
            return []
        return [t for t in tags if counts.get(t, 0) / total >= threshold]

    app_tags = filter_by_coverage(appearance_tags, tag_counts, threshold)
    cloth_tags = filter_by_coverage(clothing_tags, tag_counts, threshold)

    result = character_tag
    if app_tags:
        result += ', ' + ', '.join(app_tags)
    if cloth_tags:
        result += ' | ' + ', '.join(cloth_tags)
    return result
```

**输出示例**：

```
hu_tao_(genshin_impact), brown_hair, twin_braids, flower-shaped_pupils, red_eyes, blush | hat, shorts, vest, boots, red_neckwear
```

> 外貌区：发色 → 发型 → 瞳色 → 面部特征 | 服装区：按覆盖率高→低

#### 角色输出格式 (JSON)

```json
{
  "_meta": {
    "source": "danbooru.donmai.us",
    "fetched_at": "2026-06-01T12:00:00Z",
    "total_series": 30,
    "method": "posts_extraction + suffix_search + wiki + tag_classification"
  },
  "series": {
    "re_zero": [
      {
        "tag": "pandora_(re:zero)",
        "english_name": "Pandora",
        "source": "Re:Zero Kara Hajimeru Isekai Seikatsu",
        "post_count": 145,
        "description": "A character from Re:Zero... She is the Witch of Vainglory.",
        "appearance_tags": ["blue_eyes", "small_breasts", "very_long_hair", "grey_hair"],
        "clothing_tags": ["white_dress", "blue_hair_ribbon", "barefoot"],
        "excluded_count": 18
      }
    ],
    "genshin_impact": [...]
  }
}
```

---

## 输出格式

爬取结果统一保存为 JSON：

```json
{
  "_meta": {
    "source": "danbooru.donmai.us",
    "fetched_at": "2026-06-01T12:00:00Z",
    "category": "hair_color",
    "pattern": "*_hair",
    "total": 120
  },
  "tags": [
    {"name": "blonde_hair", "count": 1234567, "category": 0}
  ]
}
```

## 常见 pattern 速查

| 需求 | pattern |
|------|---------|
| 发色 | `*_hair` |
| 瞳色 | `*_eyes` |
| 发型 | `*_ponytail OR *_bangs OR *_braid OR *_bun OR *_twintails` |
| 服装-连衣裙 | `*_dress` |
| 服装-上衣 | `*_shirt OR *_jacket OR *_sweater OR *_hoodie OR *_blouse` |
| 服装-下装 | `*_skirt OR *_pants OR *_shorts` |
| 服装-鞋袜 | `*_shoes OR *_boots OR *_socks OR *_thighhighs OR *_stockings` |
| 表情 | `*_expression OR *smile* OR *blush* OR *frown* OR *angry* OR *cry* OR *laugh*` |
| 姿势 | `*standing* OR *sitting* OR *lying* OR *_pose` |
| 配饰 | `*_ribbon OR *_bow OR *_hat OR *_glasses OR *_necklace OR *_earrings` |
| 背景 | `*_background OR *_sky OR *outdoor* OR *indoor* OR *_room OR *_scenery` |
| 视角 | `*cowboy_shot* OR *close-up* OR *full_body* OR *from_above* OR *from_below*` |
| 系列(copyright) | `search[category]=3` |
| 角色(character) | `search[category]=4` |
| 系列→角色（帖子提取） | 搜 `posts.json?tags=<copyright_tag>` → `tag_string_character` |
| 系列→角色（通配符） | `search[name_matches]=*(<suffix>)&search[category]=4` |

## 响应格式

### 单角色标签查询（紧凑输出）

用户给出角色名（中/英）时，**默认只输出紧凑三区 tag 串**，不展开分类表格和 wiki 翻译：

```
<专有角色标签>, <外貌tag1>, <外貌tag2>, ... | <服装tag1>, <服装tag2>, ...
```

三区含义：
- **角色区** — 角色专有标签（如 `hu_tao_(genshin_impact)`）
- **外貌区** — 发色/瞳色/发型/面部特征/体型等人物固有外观
- **服装区** — 所有穿戴物（上衣/下装/连衣裙/鞋袜/配饰/帽子/眼镜…）

规则：
- 外貌区和服装区之间用 ` | ` 分隔
- 各区内部按覆盖率从高到低排列，阈值 ≥ 15%
- **强制剔除以下与人物特征无关的标签**：`solo`、`looking_at_viewer`、`smile`、`simple_background`、`white_background`、`gradient_background`、所有 `*_background`、`standing`、`sitting`、`arms_up`、`hands_up`、`from_above`、`from_below`、`cowboy_shot`、`close-up`、`full_body`、`dutch_angle`、`open_mouth`、`:d`、`:o`、`absurdres`、`highres`、`monochrome`、`sketch`、`weapon`、`*holding*`、`holding_*`、`holding`、`watermark`、`signature`、`commentary_request`、`bad_id`、`translated`、`official_art`
- 不在 tag 串中夹杂解释文字
- 若用户说"完整画像""对比""详细"才展开分类表格

### 多角色/批量输出

多个角色时逐个输出三区 tag 串，角色名加粗标注，不合并为长表格。

---

## 陷阱

1. **代理是刚需**：不走代理必定超时；terminal 的 curl 被工具层拦截时，切用 `execute_code` + Python `urllib`。
2. **通配符仅 `*`**：`name_matches` 不支持正则，仅 `*` 通配。
3. **`*_hair` 会误匹配**：如 `*_hair_ornament`，需后过滤或精确化 pattern。
4. **分页上限**：tags API 最多 1000 页（每页 100 条=10万条），大量标签需拆分查询。
5. **废弃标签**：检查 `is_deprecated` 字段，不纳入词典。
6. **`category_name` 不可靠**：以 `category` 数字为准。
7. **角色标签两大形态**：`角色名_(系列)` 是标准格式，但也有不带括号的短名（如 `natsuki_subaru` 而非 `natsuki_subaru_(re:zero)`），帖子提取路线能覆盖这类，通配符路线会漏。
8. **系列后缀不一定是 copyright tag**：如 copyright tag 是 `re_zero`，但角色标签后缀是 `(re:zero)`（冒号），需要兼容两种写法。
9. **角色 wiki 请求量大**：每个角色一个 HTTP 请求，批量时需控制速率。只对高频角色（Top 20）查 wiki，低频角色仅保留 tag 名和频次。
10. **`original` 系列陷阱**：`original` 是 Danbooru 上最大的 copyright 标签（150万帖），但它是「原创」而非具体系列，从中提取的角色标签质量低、零散，应跳过或单独处理。
11. **低帖量角色统计不可靠**：帖量 < 100 的角色（如 Cecilia 88帖），标签波动极大——发色/瞳色/服装统计无意义。此时以 wiki 描述为准，辅以频次最高的几个标签。
12. **copyright tag 格式多样**：`re_zero`（下划线）、`honkai:_star_rail`（冒号）、`zenless_zone_zero`（下划线）各不相同。搜角色前必须先查 category=3 确认准确的 copyright tag 拼写，不要猜测。

## 验证

爬取完成后：
- 打印 `total` 确认标签数量
- 随机抽 5 个标签检查 `post_count > 0`
- 检查无 deprecated / 重复 name
