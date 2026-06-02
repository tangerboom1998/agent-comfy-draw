"""Character Query — Tanger-Presets-Show 角色查询工具.

独立解析 Tanger-Presets-Show 的 characterList.js，支持按角色名/系列名模糊搜索。
不依赖 pretags.json，直接读取原始数据。

用法：
    python character_query.py "角色名"           # 精确/模糊搜索
    python character_query.py --series "系列名"   # 按系列搜索
    python character_query.py --random "系列名"   # 随机选一个
    python character_query.py --list-series       # 列出所有系列
    python character_query.py --stats             # 统计信息
"""

from __future__ import annotations

import json
import re
import argparse
import random
from pathlib import Path
from typing import Optional

_SKILL_ROOT = Path(__file__).resolve().parent.parent
_DATA_FILE = _SKILL_ROOT / "Tanger-Presets-Show" / "data" / "characterList.js"


class CharacterDB:
    """Tanger-Presets-Show 角色数据库."""

    def __init__(self, data_path: str | Path | None = None):
        if data_path is None:
            data_path = _DATA_FILE
        self.data_path = Path(data_path)
        self._chars: list[dict] = []
        self._series_map: dict[str, list[dict]] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        with open(self.data_path, 'r', encoding='utf-8') as f:
            content = f.read()
        json_str = re.sub(r'^var\s+_characterList\s*=\s*', '', content).rstrip().rstrip(';')
        self._chars = json.loads(json_str)
        # 构建系列索引
        for item in self._chars:
            parts = [p.strip() for p in item['prompt'].split(',')]
            series = parts[1].replace('\\(', '(').replace('\\)', ')') if len(parts) > 1 else 'Unknown'
            if series not in self._series_map:
                self._series_map[series] = []
            self._series_map[series].append(item)
        self._loaded = True

    @property
    def total(self) -> int:
        self._ensure_loaded()
        return len(self._chars)

    @property
    def series_list(self) -> list[str]:
        self._ensure_loaded()
        return sorted(self._series_map.keys())

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """按角色名或系列名模糊搜索."""
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        for item in self._chars:
            prompt = item['prompt']
            if query_lower in prompt.lower():
                results.append(self._format_result(item))
                if len(results) >= limit:
                    break
        return results

    def search_by_series(self, series: str, limit: int = 50) -> list[dict]:
        """按系列名搜索所有角色."""
        self._ensure_loaded()
        series_lower = series.lower()
        results = []
        for s, items in self._series_map.items():
            if series_lower in s.lower():
                for item in items[:limit]:
                    results.append(self._format_result(item))
        return results[:limit]

    def random_from_series(self, series: str) -> Optional[dict]:
        """从指定系列随机选一个角色."""
        self._ensure_loaded()
        series_lower = series.lower()
        candidates = []
        for s, items in self._series_map.items():
            if series_lower in s.lower():
                candidates.extend(items)
        if not candidates:
            return None
        return self._format_result(random.choice(candidates))

    def get_by_name(self, name: str) -> Optional[dict]:
        """精确查找角色（英文名）."""
        self._ensure_loaded()
        name_lower = name.lower()
        for item in self._chars:
            parts = [p.strip() for p in item['prompt'].split(',')]
            char_name = parts[0].replace('\\(', '(').replace('\\)', ')') if parts else ''
            if char_name.lower() == name_lower:
                return self._format_result(item)
        return None

    def _format_result(self, item: dict) -> dict:
        """格式化返回结果."""
        prompt = item['prompt']
        parts = [p.strip() for p in prompt.split(',')]
        char_name = parts[0].replace('\\(', '(').replace('\\)', ')') if parts else ''
        series = parts[1].replace('\\(', '(').replace('\\)', ')') if len(parts) > 1 else ''
        tags = ', '.join(parts[2:]) if len(parts) > 2 else ''
        return {
            'file': item['file'],
            'name': char_name,
            'series': series,
            'tags': tags,
            'prompt': prompt.replace('\\(', '(').replace('\\)', ')'),
        }


# 便捷单例
_db: CharacterDB | None = None

def get_db() -> CharacterDB:
    global _db
    if _db is None:
        _db = CharacterDB()
    return _db


def search(query: str, limit: int = 20) -> list[dict]:
    return get_db().search(query, limit)

def search_series(series: str, limit: int = 50) -> list[dict]:
    return get_db().search_by_series(series, limit)

def random_character(series: str) -> Optional[dict]:
    return get_db().random_from_series(series)


# CLI
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Tanger-Presets-Show 角色查询工具')
    parser.add_argument('query', nargs='?', help='角色名或关键词')
    parser.add_argument('--series', '-s', help='按系列搜索')
    parser.add_argument('--random', '-r', help='从系列中随机选一个')
    parser.add_argument('--list-series', '-l', action='store_true', help='列出所有系列')
    parser.add_argument('--stats', action='store_true', help='统计信息')
    parser.add_argument('--limit', type=int, default=20, help='结果数量限制')
    parser.add_argument('--json', action='store_true', help='JSON 输出')
    args = parser.parse_args()

    db = get_db()

    if args.stats:
        print(f"角色总数: {db.total}")
        print(f"系列总数: {len(db.series_list)}")
        # 热门前10系列
        top = sorted(db._series_map.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print("\n热门系列 Top 10:")
        for s, items in top:
            print(f"  {s}: {len(items)} 角色")
    elif args.list_series:
        for s in db.series_list:
            print(f"{s} ({len(db._series_map[s])})")
    elif args.random:
        result = db.random_from_series(args.random)
        if result:
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"角色: {result['name']}")
                print(f"系列: {result['series']}")
                print(f"Prompt: {result['prompt']}")
        else:
            print(f"未找到系列: {args.random}")
    elif args.series:
        results = db.search_by_series(args.series, args.limit)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"系列 '{args.series}' 找到 {len(results)} 个角色:")
            for r in results:
                print(f"  {r['name']} | {r['tags'][:60]}...")
    elif args.query:
        results = db.search(args.query, args.limit)
        if args.json:
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"搜索 '{args.query}' 找到 {len(results)} 个结果:")
            for r in results:
                print(f"  [{r['series']}] {r['name']}")
    else:
        parser.print_help()
