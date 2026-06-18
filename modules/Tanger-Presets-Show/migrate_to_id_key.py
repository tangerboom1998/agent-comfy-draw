#!/usr/bin/env python3
"""
数据迁移脚本：将 pretags.json 从 name-key 结构迁移到 id-key 结构
- 人物类：{"characters": {"卡片名": {...}}} -> {"characters": {"abc12345": {...}}}
- 标签类：{"categories": {"分类": {"标签名": {...}}}} -> {"categories": {"分类": {"def67890": {...}}}}
"""
import json
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

def _resolve_data_path() -> str:
    """解析 pretags.json 路径：PRETAGS_DATA_PATH 环境变量 > 向上搜索 pretags/ 目录。"""
    env_path = os.getenv('PRETAGS_DATA_PATH')
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return env_path
        elif p.is_dir():
            json_files = sorted(p.glob('*.json'))
            if json_files:
                return str(json_files[0])
    # 向上搜索 pretags/ 目录
    start = Path(__file__).resolve().parent
    for p in [start, *start.parents]:
        pretags_dir = p / 'pretags'
        if pretags_dir.is_dir():
            json_files = sorted(pretags_dir.glob('*.json'))
            if json_files:
                return str(json_files[0])
    raise RuntimeError(
        "未找到 pretags 数据文件。请设置 PRETAGS_DATA_PATH 环境变量，"
        "或将数据文件放在项目根目录的 pretags/ 文件夹中。"
    )

DATA_PATH = _resolve_data_path()

def generate_card_id(card_type, **fields):
    """生成卡片ID（8位hash）"""
    if card_type == 'character':
        text = f"{fields.get('cname', '')}{fields.get('name', '')}{fields.get('source', '')}"
    else:
        text = f"{fields.get('name', '')}{fields.get('tag', '')}"
    
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

def migrate_characters(old_characters):
    """迁移人物卡片：name-key -> id-key"""
    new_characters = {}
    name_to_id_map = {}  # 用于更新 series 引用
    
    print(f"开始迁移 {len(old_characters)} 个人物卡片...")
    
    for i, (cname, char_data) in enumerate(old_characters.items(), 1):
        # 生成ID
        card_id = generate_card_id('character',
            cname=char_data.get('cname', cname),
            name=char_data.get('name', ''),
            source=char_data.get('source', ''))
        
        # 添加ID字段到卡片数据
        char_data['id'] = card_id
        
        # 使用ID作为key
        new_characters[card_id] = char_data
        name_to_id_map[cname] = card_id
        
        if i % 1000 == 0:
            print(f"  已处理 {i}/{len(old_characters)} 个人物卡片...")
    
    print(f"✓ 人物卡片迁移完成")
    return new_characters, name_to_id_map

def migrate_categories(old_categories):
    """迁移标签卡片：name-key -> id-key"""
    new_categories = {}
    
    total_tags = sum(len(tags) for tags in old_categories.values())
    print(f"开始迁移 {len(old_categories)} 个分类，共 {total_tags} 个标签...")
    
    processed = 0
    for cat_name, tags in old_categories.items():
        new_categories[cat_name] = {}
        
        for tag_name, tag_data in tags.items():
            # 生成ID
            card_id = generate_card_id('tag',
                name=tag_data.get('name', tag_name),
                tag=tag_data.get('tag', ''))
            
            # 添加ID字段到标签数据
            tag_data['id'] = card_id
            
            # 使用ID作为key
            new_categories[cat_name][card_id] = tag_data
            
            processed += 1
            if processed % 1000 == 0:
                print(f"  已处理 {processed}/{total_tags} 个标签...")
    
    print(f"✓ 标签卡片迁移完成")
    return new_categories

def update_series(old_series, name_to_id_map):
    """更新 series 索引，将 character name 引用改为 ID"""
    new_series = {}
    
    print(f"开始更新 {len(old_series)} 个系列索引...")
    
    for series_name, series_data in old_series.items():
        new_series[series_name] = {
            'name': series_data.get('name', series_name),
            'count': series_data.get('count', 0),
            'characters': []
        }
        
        # 将角色名转换为ID
        for char_name in series_data.get('characters', []):
            if char_name in name_to_id_map:
                new_series[series_name]['characters'].append(name_to_id_map[char_name])
            else:
                print(f"  警告: 系列 '{series_name}' 中的角色 '{char_name}' 未找到对应ID")
    
    print(f"✓ 系列索引更新完成")
    return new_series

def main():
    print("=" * 60)
    print("数据迁移：name-key -> id-key")
    print("=" * 60)
    
    # 读取原始数据
    print(f"\n读取数据文件: {DATA_PATH}")
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 文件不存在 {DATA_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"错误: 读取文件失败 - {e}")
        sys.exit(1)
    
    print(f"✓ 数据文件读取成功")
    
    # 迁移人物卡片
    print("\n" + "=" * 60)
    old_characters = old_data.get('characters', {})
    new_characters, name_to_id_map = migrate_characters(old_characters)
    
    # 迁移标签卡片
    print("\n" + "=" * 60)
    old_categories = old_data.get('categories', {})
    new_categories = migrate_categories(old_categories)
    
    # 更新系列索引
    print("\n" + "=" * 60)
    old_series = old_data.get('series', {})
    new_series = update_series(old_series, name_to_id_map)
    
    # 构建新数据结构
    new_data = {
        'characters': new_characters,
        'categories': new_categories,
        'series': new_series
    }
    
    # 保留其他字段
    for key in old_data:
        if key not in ['characters', 'categories', 'series']:
            new_data[key] = old_data[key]
    
    # 写入新数据
    print("\n" + "=" * 60)
    print(f"写入迁移后的数据到: {DATA_PATH}")
    try:
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 数据写入成功")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        sys.exit(1)
    
    # 统计信息
    print("\n" + "=" * 60)
    print("迁移统计:")
    print(f"  人物卡片: {len(old_characters)} -> {len(new_characters)}")
    print(f"  标签分类: {len(old_categories)}")
    total_old_tags = sum(len(tags) for tags in old_categories.values())
    total_new_tags = sum(len(tags) for tags in new_categories.values())
    print(f"  标签总数: {total_old_tags} -> {total_new_tags}")
    print(f"  系列索引: {len(old_series)} -> {len(new_series)}")
    print("=" * 60)
    print("✓ 迁移完成！")
    print(f"备份文件位于: {Path(DATA_PATH).parent} 目录")

if __name__ == '__main__':
    main()
