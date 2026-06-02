#!/usr/bin/env python3
"""迁移脚本：将 pretags JSON 中的分类键名从中文改为英文。

映射：
  动作 → action
  服装 → clothing
  镜头 → shot
  画风 → style
  场景 → scene
  其他 → other

用法：
  python migrate_category_keys.py [input.json] [output.json]

  不传参数时，默认读取 ../../pretags/pretags-ill-noob.json，
  输出到同目录（原地覆盖需显式指定）。
"""

import json
import sys
import os
from pathlib import Path

CATEGORY_KEY_MAP = {
    '动作': 'action',
    '服装': 'clothing',
    '镜头': 'shot',
    '画风': 'style',
    '场景': 'scene',
    '其他': 'other',
}


def migrate(data: dict) -> dict:
    """迁移数据中的分类键名。"""
    if 'categories' not in data:
        print("[警告] 数据中没有 'categories' 键，跳过迁移")
        return data

    old_cats = data['categories']
    new_cats = {}

    for old_key, entries in old_cats.items():
        new_key = CATEGORY_KEY_MAP.get(old_key, old_key)
        new_cats[new_key] = entries
        count = len(entries) if isinstance(entries, dict) else 0
        print(f"  {old_key} → {new_key}  ({count} 条)")

    data['categories'] = new_cats
    return data


def main():
    default_input = str(Path(__file__).resolve().parent.parent.parent / 'pretags' / 'pretags-ill-noob.json')
    input_path = sys.argv[1] if len(sys.argv) > 1 else default_input
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path  # 默认原地覆盖

    print(f"读取: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"迁移分类键名:")
    data = migrate(data)

    print(f"写入: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 验证
    with open(output_path, 'r', encoding='utf-8') as f:
        verify = json.load(f)
    new_keys = list(verify.get('categories', {}).keys())
    print(f"验证 - 新分类键: {new_keys}")
    print("✅ 迁移完成")


if __name__ == '__main__':
    main()
