---
name: danbooru-tag-scraper
description: "Danbooru 标签爬取工具：通过代理访问 Danbooru API，按类别批量爬取标签，构建 AI 绘图 prompt 标签词典。支持角色标签提取、关联标签发现、标签分类。"
version: 1.0.0
metadata:
  openclaw:
    emoji: "🏷️"
    requires:
      env: ["HTTPS_PROXY"]
---

# Danbooru Tag Scraper

Danbooru 标签爬取工具，从 Danbooru 获取精细化标签用于 AI 绘图 prompt 构建。

## 🚀 快速开始

```bash
# 设置代理（必需）
export HTTPS_PROXY=http://127.0.0.1:7890

# 爬取发色标签
cd modules/danbooru-tag-scraper/scripts
python danbooru.py tags --pattern "*_hair" --category 0 --min-posts 500

# 提取角色标签
python danbooru.py characters --series "genshin_impact" --limit 20
```

## 🎯 核心功能

- **标签搜索** - 按通配符和类别批量爬取标签
- **角色提取** - 从系列作品中提取角色标签
- **关联标签** - 发现与指定标签高度相关的其他标签
- **标签分类** - 自动将标签分为外貌和服装类别
- **词典构建** - 构建分类型的标签词典 JSON

## ⚙️ 环境配置

**必需环境变量**:
- `HTTPS_PROXY` 或 `ALL_PROXY` - 代理地址（Danbooru 需要代理访问）
  - 示例: `http://127.0.0.1:7890`

**依赖**:
- Python 3.8+
- 无额外依赖（使用标准库 urllib）

**速率控制**:
- 连续请求间隔 ≥ 1 秒
- 批量爬取每 10 个请求 sleep 2 秒
- 单次脚本不超过 100 个请求

## 📖 使用示例

### 场景 1: 按类别爬取标签

```python
import urllib.request
import json
import time
import os

# 配置代理
PROXY = os.environ.get('HTTPS_PROXY', 'http://127.0.0.1:7890')
proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)

# 爬取发色标签
def fetch_tags(pattern, min_posts=100):
    url = f'https://danbooru.donmai.us/tags.json?search[name_matches]={pattern}&search[order]=count&limit=100'
    resp = opener.open(url, timeout=15)
    data = json.loads(resp.read())
    return [t for t in data if t['post_count'] >= min_posts]

# 示例：获取所有发色标签
tags = fetch_tags('*_hair', min_posts=500)
for t in sorted(tags, key=lambda x: -x['post_count'])[:10]:
    print(f"{t['name']}: {t['post_count']}")
```

### 场景 2: 从系列提取角色

```python
# 从系列帖子中提取角色标签
def extract_characters(series_tag, max_posts=200):
    from collections import Counter
    char_counter = Counter()
    
    url = f'https://danbooru.donmai.us/posts.json?tags={series_tag}&limit=100'
    resp = opener.open(url, timeout=15)
    posts = json.loads(resp.read())
    
    for post in posts:
        chars = post.get('tag_string_character', '').split()
        char_counter.update(chars)
    
    return char_counter

# 示例：提取原神角色
chars = extract_characters('genshin_impact', max_posts=200)
for char, count in chars.most_common(10):
    print(f"{char}: {count}")
```

### 场景 3: 构建标签词典

```python
def build_tag_dict():
    """构建分类标签词典"""
    categories = {
        'hair_color': '*_hair',
        'eye_color': '*_eyes',
        'clothing_dress': '*_dress',
        'clothing_footwear': '*_boots OR *_shoes',
        'expression': '*smile* OR *blush*',
    }
    
    result = {}
    for cat_name, pattern in categories.items():
        tags = fetch_tags(pattern, min_posts=200)
        result[cat_name] = [{'name': t['name'], 'count': t['post_count']} for t in tags]
        print(f"[{cat_name}] {len(tags)} tags")
        time.sleep(2)
    
    return result
```

## 🔧 标签类别

| 类别值 | 含义 | 示例 |
|--------|------|------|
| 0 | general | 1girl, dress, blue_eyes, smile |
| 1 | artist | kyogoku_shin, wlop |
| 3 | copyright | genshin_impact, blue_archive |
| 4 | character | hatsune_miku, hu_tao_(genshin_impact) |
| 5 | meta | highres, commentary |

## 📋 常用搜索模式

| 需求 | Pattern |
|------|---------|
| 发色 | `*_hair` |
| 瞳色 | `*_eyes` |
| 发型 | `*_ponytail OR *_braid OR *_bun` |
| 连衣裙 | `*_dress` |
| 上衣 | `*_shirt OR *_jacket OR *_sweater` |
| 鞋袜 | `*_boots OR *_shoes OR *_socks` |
| 配饰 | `*_ribbon OR *_bow OR *_hat` |

## 📚 相关文档

- [Danbooru API 官方文档](https://danbooru.donmai.us/wiki_pages/help:api)
- [Pretags 数据管理](../../references/pretags-data-management.md)
- [标签分类规则](../../references/tag-classification-rules.md)

## 📄 许可证

MIT License
