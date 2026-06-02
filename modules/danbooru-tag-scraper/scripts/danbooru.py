#!/usr/bin/env python3
"""
Danbooru Tag Scraper — 精细化标签爬取 CLI 工具。

通过代理访问 Danbooru API，按类别批量爬取标签，构建 AI 绘图 prompt 标签词典。
支持标签搜索、关联标签发现、帖子标签提取、角色标签三步法。

Usage:
  python danbooru.py tags --pattern "*_hair" --category 0 --min-posts 500
  python danbooru.py tags-from-posts --query "blue_archive" --max-posts 200
  python danbooru.py related --tag "blonde_hair" --category general
  python danbooru.py build-dict --output danbooru_tags.json
  python danbooru.py tag-info --tag "blonde_hair"
  python danbooru.py top-series --n 50 --min-posts 1000
  python danbooru.py chars-from-series --series "genshin_impact" --max-posts 300
  python danbooru.py chars-by-suffix --suffix "genshin_impact"
  python danbooru.py char-info --tag "hu_tao_(genshin_impact)"
  python danbooru.py build-char-dict --output characters.json --top-n 30
  python danbooru.py filter-tags --input tags.json --output filtered.json
  python danbooru.py format-tagline --char-tag "hu_tao_(genshin_impact)" \\
      --appearance "brown_hair,twin_braids,red_eyes" --clothing "hat,shorts,vest"

环境变量:
  HTTPS_PROXY  代理地址（第1优先）
  ALL_PROXY    代理地址（第2优先，fallback）
  默认值: http://127.0.0.1:7890
"""

import argparse
import fnmatch
import json
import os
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

# ── Base URL ──
BASE_URL = "https://danbooru.donmai.us"

# ── Proxy ──
def _get_proxy() -> str:
    return os.environ.get("HTTPS_PROXY") or os.environ.get("ALL_PROXY") or "http://127.0.0.1:7890"

def _build_opener():
    proxy = _get_proxy()
    proxy_handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    return urllib.request.build_opener(proxy_handler)

# ── Rate limiting ──
_REQUEST_COUNT = 0

def _rate_limit():
    global _REQUEST_COUNT
    _REQUEST_COUNT += 1
    if _REQUEST_COUNT > 1:
        time.sleep(1)
    if _REQUEST_COUNT % 10 == 0:
        time.sleep(2)

# ── Helpers ──

def _api_get(path: str, timeout: int = 15) -> dict | list:
    """GET request to Danbooru API with rate limiting."""
    opener = _build_opener()
    url = f"{BASE_URL}{path}"
    _rate_limit()
    resp = opener.open(url, timeout=timeout)
    return json.loads(resp.read())

# ── Exclude patterns ──
EXCLUDE_PATTERNS = [
    # 构图 / 场景
    "solo", "looking_at_viewer", "*_background", "simple_background",
    "white_background", "gradient_background",
    # 姿势 / 动作
    "standing", "sitting", "lying", "kneeling", "squatting",
    "arms_up", "hands_up", "*hand_on_*", "arms_behind_back", "crossed_arms",
    # 视角
    "from_above", "from_below", "cowboy_shot", "close-up", "full_body",
    "wide_shot", "dutch_angle", "head_out_of_frame", "profile",
    # 表情（通用类，非角色特有）
    "smile", ":d", ":o", ":3", ":q", ":p",
    # 画质 / 元数据
    "absurdres", "highres", "monochrome", "greyscale", "sketch",
    "watermark", "signature", "signed", "commentary_request", "bad_id",
    "translated", "official_art", "cover", "artist_name",
    # 武器 / 手持物（非角色固有外观）
    "weapon", "*_holding", "holding_*", "holding",
    # 光影 / 特效
    "*_focus", "light_particles", "*_lighting", "*_light",
    # 计数标签
    "1girl", "1boy", "1other", "multiple_girls", "multiple_boys",
]

# ═══════════════════════════════════════════════════════════════════
# Workflow 1: 按通配符批量爬标签
# ═══════════════════════════════════════════════════════════════════

def fetch_all_tags(pattern: str, category: int | None = None, min_posts: int = 100) -> list[dict]:
    """爬取匹配 pattern 的全部标签"""
    all_tags: list[dict] = []
    page = 1

    while True:
        params = f"search[name_matches]={urllib.request.quote(pattern)}&search[order]=count&limit=100&page={page}"
        if category is not None:
            params += f"&search[category]={category}"

        data = _api_get(f"/tags.json?{params}")
        if not data:
            break

        for t in data:
            if t["post_count"] >= min_posts and not t.get("is_deprecated", False):
                all_tags.append(t)

        if len(data) < 100:
            break
        page += 1

    return all_tags


# ═══════════════════════════════════════════════════════════════════
# Workflow 2: 按帖子提取标签集
# ═══════════════════════════════════════════════════════════════════

def extract_tags_from_posts(tag_query: str, max_posts: int = 100) -> Counter:
    """从匹配帖子中提取所有标签并统计频次"""
    tag_counter: Counter = Counter()
    page = 1
    collected = 0

    while collected < max_posts:
        data = _api_get(
            f"/posts.json?tags={urllib.request.quote(tag_query)}&limit=100&page={page}"
        )
        if not data:
            break

        for post in data:
            tags = post.get("tag_string", "").split()
            tag_counter.update(tags)

        collected += len(data)
        if len(data) < 100:
            break
        page += 1

    return tag_counter


# ═══════════════════════════════════════════════════════════════════
# Workflow 3: 获取关联标签
# ═══════════════════════════════════════════════════════════════════

def get_related_tags(tag: str, category: str = "general") -> list[dict]:
    """获取指定标签的关联标签"""
    return _api_get(
        f"/related_tag.json?query={urllib.request.quote(tag)}&category={category}"
    )


# ═══════════════════════════════════════════════════════════════════
# Workflow 4: 构建分类标签词典
# ═══════════════════════════════════════════════════════════════════

CATEGORY_PATTERNS = {
    "hair_color": "*_hair",
    "eye_color": "*_eyes",
    "hairstyle": "*_ponytail OR *_bangs OR *_braid OR *_bun OR *_twintails OR *_bob",
    "clothing_dress": "*_dress",
    "clothing_upper": "*_shirt OR *_jacket OR *_sweater OR *_hoodie OR *_blouse OR *_vest",
    "clothing_lower": "*_skirt OR *_pants OR *_shorts",
    "clothing_footwear": "*_shoes OR *_boots OR *_socks OR *_thighhighs OR *_stockings",
    "expression": "*_expression OR *smile* OR *blush* OR *frown* OR *angry* OR *cry* OR *laugh*",
    "pose": "*standing* OR *sitting* OR *lying* OR *_pose OR *arms_up* OR *hand*",
    "accessories": "*_ribbon OR *_bow OR *_hat OR *_glasses OR *_necklace OR *_earrings",
    "background": "*_background OR *_sky OR *outdoor* OR *indoor* OR *_room OR *_scenery",
    "viewpoint": "*cowboy_shot* OR *close-up* OR *full_body* OR *from_above* OR *from_below*",
}


def build_tag_dict(output_path: str = "danbooru_tags.json") -> dict:
    """构建分类型的标签词典"""
    result: dict = {}
    for cat_name, pattern in CATEGORY_PATTERNS.items():
        tags = fetch_all_tags(pattern, category=0, min_posts=200)
        result[cat_name] = [{"name": t["name"], "count": t["post_count"]} for t in tags]
        print(f"[{cat_name}] fetched {len(tags)} tags", file=sys.stderr)
        time.sleep(2)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "_meta": {
                    "source": "danbooru.donmai.us",
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                },
                **result,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    return result


# ═══════════════════════════════════════════════════════════════════
# Workflow 5: 标签详情查询
# ═══════════════════════════════════════════════════════════════════

def get_tag_info(tag_name: str) -> dict:
    """获取标签完整信息（wiki + 别名）"""
    info: dict = {"tag": tag_name, "wiki": None, "aliases_from": []}

    # Wiki
    try:
        wiki = _api_get(
            f"/wiki_pages/{urllib.request.quote(tag_name)}.json", timeout=10
        )
        info["wiki"] = wiki.get("body", "")
    except Exception:
        pass

    # Aliases
    try:
        aliases = _api_get(
            f"/tag_aliases.json?search[consequent_name]={urllib.request.quote(tag_name)}&limit=20",
            timeout=10,
        )
        info["aliases_from"] = [a["antecedent_name"] for a in aliases]
    except Exception:
        pass

    return info


# ═══════════════════════════════════════════════════════════════════
# Workflow 6: 角色标签三步法
# ═══════════════════════════════════════════════════════════════════

# Step 1 — 爬取系列列表
def get_top_series(n: int = 50, min_posts: int = 1000) -> list[dict]:
    """获取热门系列列表 (category=3, copyright)"""
    series: list[dict] = []
    page = 1
    while len(series) < n:
        data = _api_get(
            f"/tags.json?search[category]=3&search[order]=count&search[hide_empty]=true"
            f"&limit=100&page={page}"
        )
        if not data:
            break
        for t in data:
            if t["post_count"] >= min_posts and not t.get("is_deprecated"):
                series.append({"name": t["name"], "posts": t["post_count"]})
                if len(series) >= n:
                    break
        page += 1
    return series


# Step 2A — 路线 A：帖子提取
def extract_characters_from_series(series_tag: str, max_posts: int = 300) -> Counter:
    """从系列帖子中提取角色标签"""
    char_counter: Counter = Counter()
    collected = 0
    page = 1

    while collected < max_posts:
        data = _api_get(
            f"/posts.json?tags={urllib.request.quote(series_tag)}&limit=100&page={page}"
        )
        if not data:
            break
        for p in data:
            chars = p.get("tag_string_character", "").split()
            char_counter.update(chars)
        collected += len(data)
        if len(data) < 100:
            break
        page += 1

    return char_counter


# Step 2B — 路线 B：通配符搜索
def search_characters_by_suffix(suffix: str, min_posts: int = 5) -> list[dict]:
    """搜索 *(suffix) 格式的角色标签"""
    data = _api_get(
        f"/tags.json?search[name_matches]=*({urllib.request.quote(suffix)})"
        f"&search[category]=4&search[order]=count&search[hide_empty]=true&limit=200"
    )
    return [t for t in data if t["post_count"] >= min_posts and not t.get("is_deprecated")]


# Step 3 — 补充 wiki 信息
def get_character_info(tag_name: str) -> dict:
    """从 wiki 提取角色信息"""
    info: dict = {
        "tag": tag_name,
        "english_name": None,
        "source": None,
        "description": None,
    }

    try:
        wiki = _api_get(
            f"/wiki_pages/{urllib.request.quote(tag_name)}.json", timeout=10
        )
        body = wiki.get("body", "") or ""
        info["description"] = body

        # wiki 首句通常是 "A character from [Series Name]"
        if "character from" in body.lower():
            info["source"] = (
                body.split("character from")[1]
                .split(".")[0]
                .strip()
                .strip("[]")
                .replace("[[", "")
                .replace("]]", "")
            )

        # 英文名 = 括号前部分，首字母大写
        base_name = tag_name.split("(")[0].replace("_", " ").title()
        info["english_name"] = base_name
    except Exception:
        pass

    return info


# 完整流程
def build_character_dict(
    top_n_series: int = 30, posts_per_series: int = 300
) -> dict:
    """构建 {系列: [角色列表]} 词典"""
    result: dict = {}

    # Step 1
    series_list = get_top_series(n=top_n_series, min_posts=1000)
    print(f"Step 1: Got {len(series_list)} series", file=sys.stderr)

    for s in series_list:
        series_name = s["name"]
        print(f"\n--- {series_name} ---", file=sys.stderr)

        # Step 2A: 帖子提取
        chars = extract_characters_from_series(series_name, max_posts=posts_per_series)
        print(f"  Posts: {len(chars)} characters found", file=sys.stderr)

        # Step 2B: 通配符搜索（补充）
        suffix_chars = search_characters_by_suffix(series_name, min_posts=5)
        for c in suffix_chars:
            if c["name"] not in chars:
                chars[c["name"]] = c["post_count"]
        print(f"  After suffix merge: {len(chars)} characters", file=sys.stderr)

        # 仅保留 post_count >= 3 的角色
        chars = {k: v for k, v in chars.items() if v >= 3}

        # Step 3: 补 wiki（采样前 20 个高频角色）
        top_chars = sorted(chars.items(), key=lambda x: -x[1])[:20]
        char_entries = []
        for tag_name, count in top_chars:
            info = get_character_info(tag_name)
            info["post_count"] = count
            char_entries.append(info)
            time.sleep(0.5)

        result[series_name] = char_entries
        time.sleep(1)

    return result


# ═══════════════════════════════════════════════════════════════════
# 标签分类与去噪
# ═══════════════════════════════════════════════════════════════════

def filter_excluded(tag_counts: dict[str, int]) -> tuple[dict[str, int], dict[str, int]]:
    """硬编码剔除，返回 (remaining, excluded)"""
    remaining: dict[str, int] = {}
    excluded: dict[str, int] = {}
    for tag, count in tag_counts.items():
        if any(fnmatch.fnmatch(tag, pat) for pat in EXCLUDE_PATTERNS):
            excluded[tag] = count
        else:
            remaining[tag] = count
    return remaining, excluded


# ═══════════════════════════════════════════════════════════════════
# 格式化输出
# ═══════════════════════════════════════════════════════════════════

def format_character_tagline(
    character_tag: str,
    appearance_tags: list[str],
    clothing_tags: list[str],
    tag_counts: dict[str, int],
    threshold: float = 0.15,
) -> str:
    """将 agent 分类后的结果格式化为三区 tag 串"""

    def filter_by_coverage(tags: list[str], counts: dict[str, int]) -> list[str]:
        if not tags:
            return []
        total = sum(counts.get(t, 0) for t in tags)
        if not total:
            return []
        return [t for t in tags if counts.get(t, 0) / total >= threshold]

    app_tags = filter_by_coverage(appearance_tags, tag_counts)
    cloth_tags = filter_by_coverage(clothing_tags, tag_counts)

    result = character_tag
    if app_tags:
        result += ", " + ", ".join(app_tags)
    if cloth_tags:
        result += " | " + ", ".join(cloth_tags)
    return result


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Danbooru Tag Scraper — 精细化标签爬取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "环境变量:\n"
            "  HTTPS_PROXY  代理地址（第1优先）\n"
            "  ALL_PROXY    代理地址（第2优先）\n"
            "  默认值: http://127.0.0.1:7890"
        ),
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    # tags
    p_tags = sub.add_parser("tags", help="按通配符批量爬标签")
    p_tags.add_argument("--pattern", required=True, help="匹配模式，如 *_hair, blue_*")
    p_tags.add_argument("--category", type=int, default=None, help="标签类别 (0=general, 3=copyright, 4=character)")
    p_tags.add_argument("--min-posts", type=int, default=100, help="最小帖子数过滤")
    p_tags.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")
    p_tags.add_argument("--limit", type=int, default=None, help="限制输出条数")

    # tags-from-posts
    p_posts = sub.add_parser("tags-from-posts", help="从帖子中提取标签频次")
    p_posts.add_argument("--query", required=True, help="帖子搜索条件")
    p_posts.add_argument("--max-posts", type=int, default=100, help="最多爬取帖子数")
    p_posts.add_argument("--top", type=int, default=50, help="输出 Top N 标签")
    p_posts.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # related
    p_rel = sub.add_parser("related", help="获取关联标签")
    p_rel.add_argument("--tag", required=True, help="标签名")
    p_rel.add_argument("--category", default="general", help="关联标签类别")
    p_rel.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # build-dict
    p_dict = sub.add_parser("build-dict", help="构建分类标签词典")
    p_dict.add_argument("--output", "-o", default="danbooru_tags.json", help="输出 JSON 文件路径")
    p_dict.add_argument("--categories", nargs="*", choices=list(CATEGORY_PATTERNS.keys()),
                        default=None, help="指定爬取的类别（默认全部）")

    # tag-info
    p_info = sub.add_parser("tag-info", help="查询标签详情（wiki + 别名）")
    p_info.add_argument("--tag", required=True, help="标签名")
    p_info.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # top-series
    p_series = sub.add_parser("top-series", help="获取热门系列列表")
    p_series.add_argument("--n", type=int, default=50, help="获取系列数量")
    p_series.add_argument("--min-posts", type=int, default=1000, help="最小帖子数")
    p_series.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # chars-from-series
    p_cfs = sub.add_parser("chars-from-series", help="从系列帖子提取角色标签（路线A）")
    p_cfs.add_argument("--series", required=True, help="系列 copyright tag")
    p_cfs.add_argument("--max-posts", type=int, default=300, help="最多爬取帖子数")
    p_cfs.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # chars-by-suffix
    p_cbs = sub.add_parser("chars-by-suffix", help="通配符搜索角色标签（路线B）")
    p_cbs.add_argument("--suffix", required=True, help="系列后缀，如 genshin_impact")
    p_cbs.add_argument("--min-posts", type=int, default=5, help="最小帖子数")
    p_cbs.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # char-info
    p_ci = sub.add_parser("char-info", help="获取角色 wiki 信息")
    p_ci.add_argument("--tag", required=True, help="角色标签，如 hu_tao_(genshin_impact)")
    p_ci.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # build-char-dict
    p_bcd = sub.add_parser("build-char-dict", help="构建 {系列: [角色列表]} 词典")
    p_bcd.add_argument("--output", "-o", default="characters.json", help="输出 JSON 文件路径")
    p_bcd.add_argument("--top-n", type=int, default=30, help="爬取前 N 个系列")
    p_bcd.add_argument("--posts-per-series", type=int, default=300, help="每个系列爬取的帖子数")

    # filter-tags
    p_filter = sub.add_parser("filter-tags", help="剔除与人物特征无关的标签")
    p_filter.add_argument("--input", "-i", required=True, help="输入 JSON 文件（含 tag_counts）")
    p_filter.add_argument("--output", "-o", default=None, help="输出 JSON 文件路径")

    # format-tagline
    p_fmt = sub.add_parser("format-tagline", help="格式化三区 tag 串")
    p_fmt.add_argument("--char-tag", required=True, help="角色专有标签")
    p_fmt.add_argument("--appearance", default="", help="外貌标签，逗号分隔")
    p_fmt.add_argument("--clothing", default="", help="服装标签，逗号分隔")
    p_fmt.add_argument("--threshold", type=float, default=0.15, help="覆盖率阈值")

    # proxy info
    p_proxy = sub.add_parser("proxy", help="显示当前代理配置")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ── dispatch ──

    if args.command == "proxy":
        print(f"Proxy: {_get_proxy()}")
        return

    output_file: str | None = getattr(args, "output", None)

    if args.command == "tags":
        result = fetch_all_tags(args.pattern, args.category, args.min_posts)
        if args.limit:
            result = result[: args.limit]
        output_file = output_file or "tags.json"

    elif args.command == "tags-from-posts":
        counter = extract_tags_from_posts(args.query, args.max_posts)
        items = [{"tag": t, "count": c} for t, c in counter.most_common(args.top)]
        result = {"_meta": {"source": BASE_URL, "query": args.query, "total_posts_scanned": min(args.max_posts, _REQUEST_COUNT * 100)},
                  "tags": items}
        output_file = output_file or "post_tags.json"

    elif args.command == "related":
        result = get_related_tags(args.tag, args.category)
        output_file = output_file or "related_tags.json"

    elif args.command == "build-dict":
        selected = args.categories or list(CATEGORY_PATTERNS.keys())
        result = {}
        for cat_name in selected:
            if cat_name in CATEGORY_PATTERNS:
                tags = fetch_all_tags(CATEGORY_PATTERNS[cat_name], category=0, min_posts=200)
                result[cat_name] = [{"name": t["name"], "count": t["post_count"]} for t in tags]
                print(f"[{cat_name}] fetched {len(tags)} tags", file=sys.stderr)
                time.sleep(2)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"_meta": {"source": BASE_URL, "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                       **result}, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_file}", file=sys.stderr)
        return

    elif args.command == "tag-info":
        result = get_tag_info(args.tag)
        output_file = output_file or "tag_info.json"

    elif args.command == "top-series":
        result = get_top_series(args.n, args.min_posts)
        output_file = output_file or "top_series.json"

    elif args.command == "chars-from-series":
        counter = extract_characters_from_series(args.series, args.max_posts)
        items = [{"tag": t, "count": c} for t, c in counter.most_common()]
        result = {"_meta": {"source": BASE_URL, "series": args.series, "method": "posts_extraction"},
                  "characters": items}
        output_file = output_file or "chars_from_series.json"

    elif args.command == "chars-by-suffix":
        result = search_characters_by_suffix(args.suffix, args.min_posts)
        output_file = output_file or "chars_by_suffix.json"

    elif args.command == "char-info":
        result = get_character_info(args.tag)
        output_file = output_file or "char_info.json"

    elif args.command == "build-char-dict":
        result = build_character_dict(args.top_n, args.posts_per_series)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"_meta": {"source": BASE_URL,
                                  "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                  "total_series": len(result),
                                  "method": "posts_extraction + suffix_search + wiki"},
                       "series": result}, f, ensure_ascii=False, indent=2)
        print(f"Saved to {output_file}", file=sys.stderr)
        return

    elif args.command == "filter-tags":
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Try to find tag_counts in various formats
        tag_counts = data if isinstance(data, dict) and all(isinstance(v, int) for v in data.values()) else data.get("tag_counts", data.get("tags", {}))
        if isinstance(tag_counts, list):
            tag_counts = {item["tag"] if isinstance(item, dict) else item: item.get("count", 1) if isinstance(item, dict) else 1 for item in tag_counts}
        remaining, excluded = filter_excluded(tag_counts)
        result = {"remaining": remaining, "excluded": excluded,
                  "remaining_count": len(remaining), "excluded_count": len(excluded)}
        output_file = output_file or "filtered_tags.json"

    elif args.command == "format-tagline":
        # mock tag_counts: each tag gets count=100 for equal weight
        app_tags = [t.strip() for t in args.appearance.split(",") if t.strip()]
        cloth_tags = [t.strip() for t in args.clothing.split(",") if t.strip()]
        all_tags = app_tags + cloth_tags
        tag_counts = {t: 100 for t in all_tags}
        result_str = format_character_tagline(args.char_tag, app_tags, cloth_tags, tag_counts, args.threshold)
        print(result_str)
        return

    else:
        parser.print_help()
        sys.exit(1)

    # Write output
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved to {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
