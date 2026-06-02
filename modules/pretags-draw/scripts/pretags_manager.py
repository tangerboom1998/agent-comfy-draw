"""Pretags Manager — 预设标签库管理模块.

提供对 pretags.json 的 CRUD 操作，支持 agent 主动维护预设标签库。
支持的操作：list（列表）、search（搜索）、add（添加）、update（更新）、delete（删除）、info（详情）。

数据文件位于同级 skill 的 assets/ 目录中。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ── 数据文件路径 ──────────────────────────────────────────────────────────
_SKILL_ROOT = Path(__file__).resolve().parent.parent  # skill 根目录
_ASSETS_DIR = _SKILL_ROOT / "assets"


def _resolve_pretags_path() -> str:
    """解析 pretags.json 路径：环境变量 > 向上搜索 pretags 目录 > 向上搜索 pretags.json > 本地回退"""
    import os as _os
    # 1. 环境变量优先（现在支持目录或文件）
    env_path = _os.getenv('PRETAGS_DATA_PATH')
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return env_path
        elif p.is_dir():
            # 如果是目录，返回目录中第一个 JSON 文件
            json_files = sorted(p.glob('*.json'))
            if json_files:
                return str(json_files[0])
    # 2. 从脚本所在目录向上搜索项目根目录的 pretags 文件夹
    start = Path(__file__).resolve().parent
    for p in [start, *start.parents]:
        pretags_dir = p / 'pretags'
        if pretags_dir.is_dir():
            json_files = sorted(pretags_dir.glob('*.json'))
            if json_files:
                return str(json_files[0])
    # 3. 从脚本所在目录向上搜索项目根目录的 pretags.json（兼容旧部署）
    for p in [start, *start.parents]:
        candidate = p / 'pretags.json'
        if candidate.is_file():
            return str(candidate)
    # 4. 回退到本地 assets 目录（兼容旧部署）
    return str(_ASSETS_DIR / "pretags.json")


DEFAULT_PRETAGS_PATH = _resolve_pretags_path()

# ── 有效类别 ──────────────────────────────────────────────────────────────
VALID_CATEGORIES = ["character", "action", "clothing", "shot", "style", "scene", "other"]
CHARACTER_CATEGORY = "character"

# ── 前端格式适配 ──────────────────────────────────────────────────────────
# 前端格式: {characters: {cname: {...}}, series: {...}, categories: {动作:{...}, ...}}
# 转换为旧 flat 格式: {动作: {...}, ..., 人物: {...}, charsort: {...}}


def _adapt_frontend_to_flat(loaded: dict) -> dict:
    """前端格式 → 旧 flat 格式（内存适配，不写盘）"""
    if 'categories' not in loaded:
        return loaded  # 已是旧格式

    flat = dict(loaded['categories'])

    # 转换角色数据
    if 'characters' in loaded:
        chars = {}
        for cname, ch in loaded['characters'].items():
            chars[cname] = {
                'cname': ch.get('cname', cname),
                'Source': ch.get('source', ''),
                'Lora': 1 if ch.get('has_lora') else 0,
                'tag': ch.get('name', ''),
                'model file name': ch.get('lora_file', 0),
                'model hash': ch.get('lora_hash', 0),
                'unet weight': ch.get('unet_weight', 0),
                'clip weight': ch.get('clip_weight', 0),
                'link': ch.get('lora_link', 0),
                'name': ch.get('name', cname),
                'appearance': ch.get('appearance', ''),
                'clothing': ch.get('clothing', ''),
            }
        flat['character'] = chars

    if 'series' in loaded:
        charsort_data = {}
        for source, sdata in loaded['series'].items():
            charsort_data[source] = sdata.get('characters', [])
        flat['charsort'] = charsort_data

    return flat


def _adapt_flat_to_frontend(flat: dict) -> dict:
    """旧 flat 格式 → 前端格式（用于保存回盘）"""
    if 'categories' in flat:
        return flat  # 已是前端格式

    # 从旧格式重建前端格式
    frontend = {
        'characters': {},
        'series': {},
        'categories': {}
    }

    # 分类数据
    for cat in ['action', 'clothing', 'shot', 'style', 'scene', 'other']:
        if cat in flat:
            frontend['categories'][cat] = {}
            for tag_name, entry in flat[cat].items():
                item = {
                    'name': entry.get('cname', tag_name),
                    'tag': entry.get('tag', ''),
                    'has_lora': bool(entry.get('Lora', 0)),
                }
                if item['has_lora']:
                    item['lora_file'] = entry.get('model file name', '')
                    item['lora_hash'] = entry.get('model hash', '')
                    item['unet_weight'] = entry.get('unet weight', 0.8)
                    item['clip_weight'] = entry.get('clip weight', 0.8)
                    item['lora_link'] = entry.get('link', '')
                if '画风描述' in entry:
                    item['description'] = entry['画风描述']
                if 'd_group' in entry:
                    item['d_group'] = entry['d_group']
                frontend['categories'][cat][tag_name] = item

    # 角色数据
    if 'character' in flat:
        for cname, entry in flat['character'].items():
            frontend['characters'][cname] = {
                'cname': entry.get('cname', cname),
                'source': entry.get('Source', ''),
                'name': entry.get('name', ''),
                'appearance': entry.get('appearance', ''),
                'clothing': entry.get('clothing', ''),
                'has_lora': bool(entry.get('Lora', 0)),
                'lora_file': entry.get('model file name', '') if entry.get('Lora') else '',
                'lora_hash': entry.get('model hash', '') if entry.get('Lora') else '',
                'unet_weight': entry.get('unet weight', 0) if entry.get('Lora') else 0,
                'clip_weight': entry.get('clip weight', 0) if entry.get('Lora') else 0,
                'lora_link': entry.get('link', '') if entry.get('Lora') else '',
                'tags': [],
                'tags_count': 0,
            }

    # 系列数据
    if 'charsort' in flat:
        for source, cnames in flat['charsort'].items():
            frontend['series'][source] = {
                'name': source,
                'count': len(cnames),
                'characters': cnames
            }

    return frontend


class PretagsManager:
    """预设标签库管理器：对 pretags.json 进行 CRUD 操作。"""

    def __init__(self, json_path: str | None = None):
        """初始化管理器。

        Args:
            json_path: pretags.json 文件路径，默认使用 assets/pretags.json。
        """
        self.json_path = json_path or DEFAULT_PRETAGS_PATH
        self._data: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        """加载 pretags.json（懒加载 + 缓存）。"""
        if self._data is None:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            self._raw_format = loaded  # 保留原始（前端）格式用于保存
            self._data = _adapt_frontend_to_flat(loaded)
        return self._data

    def _save(self) -> None:
        """保存 pretags.json（前端格式写盘）并清除缓存。"""
        data = self._load()  # flat 格式
        # 重建 charsort（从人物类别自动生成）
        if CHARACTER_CATEGORY in data:
            charsort: dict[str, list[str]] = {}
            for cname, entry in data[CHARACTER_CATEGORY].items():
                source = entry.get("Source", "未知")
                if source not in charsort:
                    charsort[source] = []
                charsort[source].append(cname)
            data["charsort"] = charsort
        
        # 转换回前端格式写盘
        frontend = _adapt_flat_to_frontend(data)
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(frontend, f, ensure_ascii=False, indent=2)
        # 清除缓存，下次重新加载
        self._data = None

    def _reload(self) -> None:
        """强制重新加载。"""
        self._data = None
        self._load()

    # ── list：列出类别或条目 ──────────────────────────────────────────────

    def list_categories(self) -> str:
        """列出所有类别及条目数量。"""
        data = self._load()
        lines = ["预设标签库类别："]
        for cat in VALID_CATEGORIES:
            if cat in data:
                lines.append(f"  - {cat}: {len(data[cat])} 条目")
        if "charsort" in data:
            lines.append(f"  - charsort: {len(data['charsort'])} 来源分组")
        return "\n".join(lines)

    def list_entries(self, category: str, limit: int = 50, offset: int = 0) -> str:
        """列出指定类别的条目。

        Args:
            category: 类别名称。
            limit: 最多返回条目数，默认 50。
            offset: 偏移量，用于分页。
        """
        data = self._load()
        if category not in data:
            return f"错误：类别 '{category}' 不存在。有效类别：{', '.join(VALID_CATEGORIES)}"
        entries = data[category]
        if category == "charsort":
            # charsort 是 {Source: [cname, ...]} 结构
            keys = list(entries.keys())
            total = len(keys)
            page = keys[offset:offset + limit]
            lines = [f"charsort 来源分组（共 {total} 个，显示 {offset+1}-{min(offset+limit, total)}）："]
            for src in page:
                chars = entries[src]
                lines.append(f"  [{src}] {len(chars)} 个角色: {', '.join(chars[:5])}{'...' if len(chars) > 5 else ''}")
            return "\n".join(lines)

        keys = list(entries.keys())
        total = len(keys)
        page = keys[offset:offset + limit]
        lines = [f"类别 '{category}'（共 {total} 条，显示 {offset+1}-{min(offset+limit, total)}）："]
        for cname in page:
            entry = entries[cname]
            tag_str = str(entry.get("tag", ""))
            tag_preview = tag_str[:60]
            lora_mark = " [LoRA]" if entry.get("Lora") else ""
            lines.append(f"  - {cname}{lora_mark}: {tag_preview}{'...' if len(tag_str) > 60 else ''}")
        return "\n".join(lines)

    # ── search：搜索条目 ──────────────────────────────────────────────────

    def search(self, keyword: str, category: str | None = None, limit: int = 20) -> str:
        """搜索条目（按中文名或 tag 内容）。

        Args:
            keyword: 搜索关键词。
            category: 限定类别，None 则搜索所有类别。
            limit: 最多返回条目数。
        """
        data = self._load()
        categories = [category] if category else VALID_CATEGORIES
        results: list[tuple[str, str, dict]] = []

        for cat in categories:
            if cat not in data:
                continue
            for cname, entry in data[cat].items():
                tag_str = str(entry.get("tag", ""))
                if keyword.lower() in cname.lower() or keyword.lower() in tag_str.lower():
                    results.append((cat, cname, entry))
                    if len(results) >= limit:
                        break
            if len(results) >= limit:
                break

        if not results:
            return f"未找到匹配 '{keyword}' 的条目。"

        lines = [f"搜索 '{keyword}' 结果（共 {len(results)} 条）："]
        for cat, cname, entry in results:
            tag_str = str(entry.get("tag", ""))
            tag_preview = tag_str[:80]
            lora_mark = " [LoRA]" if entry.get("Lora") else ""
            lines.append(f"  [{cat}] {cname}{lora_mark}: {tag_preview}{'...' if len(tag_str) > 80 else ''}")
        return "\n".join(lines)

    # ── info：查看条目详情 ────────────────────────────────────────────────

    def info(self, category: str, cname: str) -> str:
        """查看条目详情。

        Args:
            category: 类别名称。
            cname: 中文名称（条目 key）。
        """
        data = self._load()
        if category not in data:
            return f"错误：类别 '{category}' 不存在。"
        if cname not in data[category]:
            return f"错误：类别 '{category}' 中不存在条目 '{cname}'。"
        entry = data[category][cname]
        lines = [f"条目详情 [{category}] {cname}："]
        for key, value in entry.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)

    # ── add：添加条目 ─────────────────────────────────────────────────────

    def add(
        self,
        category: str,
        cname: str,
        tag: str,
        lora: bool = False,
        model_file_name: str = "",
        unet_weight: float = 0.8,
        clip_weight: float = 0.8,
        link: str = "",
        model_hash: str = "",
        source: str = "",
        name: str = "",
        appearance: str = "",
        clothes: str = "",
    ) -> str:
        """添加新条目。

        Args:
            category: 类别名称（人物/动作/服装/镜头/画风/场景/其他）。
            cname: 中文名称（作为 key）。
            tag: 英文 tag 内容。
            lora: 是否为 LoRA 条目。
            model_file_name: LoRA 模型文件名（仅 LoRA 条目）。
            unet_weight: unet 权重（仅 LoRA 条目）。
            clip_weight: clip 权重（仅 LoRA 条目）。
            link: 链接（如 civitai 链接）。
            model_hash: 模型哈希。
            source: 来源（仅人物类别）。
            name: 英文角色名（仅人物类别）。
            appearance: 外貌描述（仅人物类别）。
            clothes: 服装描述（仅人物类别）。
        """
        if category not in VALID_CATEGORIES:
            return f"错误：无效类别 '{category}'。有效类别：{', '.join(VALID_CATEGORIES)}"

        data = self._load()
        if category not in data:
            data[category] = {}

        if cname in data[category]:
            return f"错误：类别 '{category}' 中已存在条目 '{cname}'。请使用 update 操作更新。"

        if category == CHARACTER_CATEGORY:
            # 人物条目结构
            entry: dict[str, Any] = {
                "cname": cname,
                "Source": source or "自定义",
                "Lora": 1 if lora else 0,
                "model file name": model_file_name or 0,
                "unet weight": unet_weight if lora else 0,
                "clip weight": clip_weight if lora else 0,
                "link": link or 0,
                "model hash": model_hash or 0,
                "name": name or cname,
                "appearance": appearance or "",
                "clothing": clothes or "",
            }
        else:
            # 非人物条目结构
            entry = {
                "cname": cname,
                "Lora": 1 if lora else 0,
                "model file name": model_file_name or 0,
                "model hash": model_hash or 0,
                "unet weight": unet_weight if lora else 0,
                "clip weight": clip_weight if lora else 0,
                "link": link or 0,
                "tag": tag,
            }

        data[category][cname] = entry
        self._data = data
        self._save()
        return f"✅ 已添加条目 [{category}] {cname}"

    # ── update：更新条目 ──────────────────────────────────────────────────

    def update(self, category: str, cname: str, **fields) -> str:
        """更新条目字段。

        Args:
            category: 类别名称。
            cname: 中文名称。
            **fields: 要更新的字段（key=value）。
        """
        if category not in VALID_CATEGORIES:
            return f"错误：无效类别 '{category}'。"

        data = self._load()
        if category not in data:
            return f"错误：类别 '{category}' 不存在。"
        if cname not in data[category]:
            return f"错误：类别 '{category}' 中不存在条目 '{cname}'。"

        entry = data[category][cname]
        updated_fields = []
        for key, value in fields.items():
            if key in entry:
                old_value = entry[key]
                entry[key] = value
                updated_fields.append(f"{key}: {old_value} → {value}")
            else:
                entry[key] = value
                updated_fields.append(f"{key}: (新增) {value}")

        if not updated_fields:
            return f"未更新任何字段。"

        data[category][cname] = entry
        self._data = data
        self._save()
        return f"✅ 已更新 [{category}] {cname}：\n" + "\n".join(f"  {f}" for f in updated_fields)

    # ── delete：删除条目 ──────────────────────────────────────────────────

    def delete(self, category: str, cname: str) -> str:
        """删除条目。

        Args:
            category: 类别名称。
            cname: 中文名称。
        """
        if category not in VALID_CATEGORIES:
            return f"错误：无效类别 '{category}'。"

        data = self._load()
        if category not in data:
            return f"错误：类别 '{category}' 不存在。"
        if cname not in data[category]:
            return f"错误：类别 '{category}' 中不存在条目 '{cname}'。"

        del data[category][cname]
        self._data = data
        self._save()
        return f"✅ 已删除 [{category}] {cname}"

    # ── stats：统计信息 ───────────────────────────────────────────────────

    def stats(self) -> str:
        """返回预设标签库统计信息。"""
        data = self._load()
        lines = ["预设标签库统计："]
        total = 0
        for cat in VALID_CATEGORIES:
            if cat in data:
                count = len(data[cat])
                total += count
                lora_count = sum(1 for e in data[cat].values() if e.get("Lora"))
                lines.append(f"  {cat}: {count} 条目（其中 LoRA: {lora_count}）")
        lines.append(f"  总计: {total} 条目")
        if "charsort" in data:
            lines.append(f"  来源分组: {len(data['charsort'])} 个来源")
        return "\n".join(lines)


# ── 便捷单例 ──────────────────────────────────────────────────────────────

_default_manager: PretagsManager | None = None


def get_pretags_manager(json_path: str | None = None) -> PretagsManager:
    """获取默认 PretagsManager 单例（延迟初始化）。"""
    global _default_manager
    if _default_manager is None or json_path is not None:
        _default_manager = PretagsManager(json_path)
    return _default_manager


# ── CLI 入口 ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python pretags_manager.py <command> [args...]")
        print("命令:")
        print("  list [category]              列出类别或条目")
        print("  search <keyword> [category]  搜索条目")
        print("  info <category> <cname>      查看条目详情")
        print("  stats                        统计信息")
        sys.exit(1)

    mgr = get_pretags_manager()
    cmd = sys.argv[1]

    if cmd == "list":
        if len(sys.argv) > 2:
            print(mgr.list_entries(sys.argv[2]))
        else:
            print(mgr.list_categories())
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("用法: search <keyword> [category]")
        else:
            cat = sys.argv[3] if len(sys.argv) > 3 else None
            print(mgr.search(sys.argv[2], category=cat))
    elif cmd == "info":
        if len(sys.argv) < 4:
            print("用法: info <category> <cname>")
        else:
            print(mgr.info(sys.argv[2], sys.argv[3]))
    elif cmd == "stats":
        print(mgr.stats())
    else:
        print(f"未知命令: {cmd}")
