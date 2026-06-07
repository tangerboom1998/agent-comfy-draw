#!/usr/bin/env python3
"""
清理 pretags-anima.json 中的 LoRA 词条

Anima 工作流使用 Flux 模型，不兼容 SDXL LoRA。
此脚本删除所有带 lora_file 的 categories 词条。
"""

import json
import os
from datetime import datetime

# 文件路径
PRETAGS_FILE = '/home/hctang/claw-build/agent-comfy-draw/pretags/pretags-anima.json'
BACKUP_FILE = f'{PRETAGS_FILE}.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}'

def main():
    print("🔍 读取 pretags-anima.json...")
    with open(PRETAGS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 创建备份
    print(f"💾 创建备份: {BACKUP_FILE}")
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 统计
    total_removed = 0
    stats = {}

    # 处理 categories
    if 'categories' in data:
        for cat_name, cat_items in data['categories'].items():
            if not isinstance(cat_items, dict):
                continue

            # 找出带 LoRA 的词条
            to_remove = []
            for item_id, item in cat_items.items():
                if isinstance(item, dict):
                    has_lora = item.get('has_lora') == True
                    has_lora_file = bool(item.get('lora_file'))

                    if has_lora or has_lora_file:
                        to_remove.append(item_id)

            # 删除
            if to_remove:
                stats[cat_name] = len(to_remove)
                total_removed += len(to_remove)

                print(f"\n📂 {cat_name}: 删除 {len(to_remove)} 个带 LoRA 的词条")

                # 显示前 5 个
                for item_id in to_remove[:5]:
                    item = cat_items[item_id]
                    print(f"  - {item.get('name', 'N/A')} (lora: {item.get('lora_file', 'N/A')})")

                if len(to_remove) > 5:
                    print(f"  ... 还有 {len(to_remove) - 5} 个")

                # 执行删除
                for item_id in to_remove:
                    del cat_items[item_id]

    # 保存清理后的文件
    print(f"\n💾 保存清理后的文件...")
    with open(PRETAGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 总结
    print(f"\n✅ 清理完成！")
    print(f"\n📊 统计:")
    for cat_name, count in stats.items():
        print(f"  - {cat_name}: {count} 个")
    print(f"\n  总计删除: {total_removed} 个带 LoRA 的词条")
    print(f"\n  原始文件大小: {os.path.getsize(BACKUP_FILE) / 1024 / 1024:.2f} MB")
    print(f"  清理后大小: {os.path.getsize(PRETAGS_FILE) / 1024 / 1024:.2f} MB")
    print(f"\n  备份文件: {BACKUP_FILE}")

if __name__ == '__main__':
    main()
