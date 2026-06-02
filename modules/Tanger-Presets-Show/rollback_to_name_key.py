#!/usr/bin/env python3
"""
数据回滚脚本：将 id-key 结构回滚到 name-key 结构（但保留ID字段）
这样前端可以继续使用name，同时数据中保留ID为未来做准备
"""
import json
import sys

DATA_PATH = 'data/pretags.json'
BACKUP_PATH = 'data/pretags_backup_before_rollback.json'

def rollback_characters(id_key_characters):
    """将人物卡片从 id-key 回滚到 name-key（保留ID字段）"""
    name_key_characters = {}
    
    print(f"开始回滚 {len(id_key_characters)} 个人物卡片...")
    
    for i, (char_id, char_data) in enumerate(id_key_characters.items(), 1):
        cname = char_data.get('cname', '')
        if not cname:
            print(f"  警告: 卡片ID {char_id} 没有cname，跳过")
            continue
        
        # 使用cname作为key，但保留ID字段
        name_key_characters[cname] = char_data
        
        if i % 1000 == 0:
            print(f"  已处理 {i}/{len(id_key_characters)} 个人物卡片...")
    
    print(f"✓ 人物卡片回滚完成")
    return name_key_characters

def rollback_categories(id_key_categories):
    """将标签从 id-key 回滚到 name-key（保留ID字段）"""
    name_key_categories = {}
    
    total_tags = sum(len(tags) for tags in id_key_categories.values())
    print(f"开始回滚 {len(id_key_categories)} 个分类，共 {total_tags} 个标签...")
    
    processed = 0
    for cat_name, tags in id_key_categories.items():
        name_key_categories[cat_name] = {}
        
        for tag_id, tag_data in tags.items():
            tag_name = tag_data.get('name', '')
            if not tag_name:
                print(f"  警告: 标签ID {tag_id} 在分类 {cat_name} 中没有name，跳过")
                continue
            
            # 使用name作为key，但保留ID字段
            name_key_categories[cat_name][tag_name] = tag_data
            
            processed += 1
            if processed % 1000 == 0:
                print(f"  已处理 {processed}/{total_tags} 个标签...")
    
    print(f"✓ 标签回滚完成")
    return name_key_categories

def rollback_series(id_key_series, id_to_name_map):
    """将系列索引从ID引用回滚到name引用"""
    name_key_series = {}
    
    print(f"开始回滚 {len(id_key_series)} 个系列索引...")
    
    for series_name, series_data in id_key_series.items():
        name_key_series[series_name] = {
            'name': series_data.get('name', series_name),
            'count': series_data.get('count', 0),
            'characters': []
        }
        
        # 将ID转换回name
        for char_id in series_data.get('characters', []):
            if char_id in id_to_name_map:
                name_key_series[series_name]['characters'].append(id_to_name_map[char_id])
            else:
                print(f"  警告: 系列 '{series_name}' 中的角色ID '{char_id}' 未找到对应name")
    
    print(f"✓ 系列索引回滚完成")
    return name_key_series

def main():
    print("=" * 60)
    print("数据回滚：id-key -> name-key（保留ID字段）")
    print("=" * 60)
    
    # 读取当前数据
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
    
    # 备份当前数据
    print(f"\n备份当前数据到: {BACKUP_PATH}")
    try:
        with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
            json.dump(old_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 备份完成")
    except Exception as e:
        print(f"错误: 备份失败 - {e}")
        sys.exit(1)
    
    # 回滚人物卡片
    print("\n" + "=" * 60)
    id_key_characters = old_data.get('characters', {})
    name_key_characters = rollback_characters(id_key_characters)
    
    # 创建ID到name的映射（用于系列索引）
    id_to_name_map = {char_data.get('id'): cname 
                      for cname, char_data in name_key_characters.items() 
                      if char_data.get('id')}
    
    # 回滚标签
    print("\n" + "=" * 60)
    id_key_categories = old_data.get('categories', {})
    name_key_categories = rollback_categories(id_key_categories)
    
    # 回滚系列索引
    print("\n" + "=" * 60)
    id_key_series = old_data.get('series', {})
    name_key_series = rollback_series(id_key_series, id_to_name_map)
    
    # 构建新数据结构
    new_data = {
        'characters': name_key_characters,
        'categories': name_key_categories,
        'series': name_key_series
    }
    
    # 保留其他字段
    for key in old_data:
        if key not in ['characters', 'categories', 'series']:
            new_data[key] = old_data[key]
    
    # 写入新数据
    print("\n" + "=" * 60)
    print(f"写入回滚后的数据到: {DATA_PATH}")
    try:
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 数据写入成功")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        sys.exit(1)
    
    # 统计信息
    print("\n" + "=" * 60)
    print("回滚统计:")
    print(f"  人物卡片: {len(id_key_characters)} -> {len(name_key_characters)}")
    print(f"  标签分类: {len(id_key_categories)}")
    total_old_tags = sum(len(tags) for tags in id_key_categories.values())
    total_new_tags = sum(len(tags) for tags in name_key_categories.values())
    print(f"  标签总数: {total_old_tags} -> {total_new_tags}")
    print(f"  系列索引: {len(id_key_series)} -> {len(name_key_series)}")
    print("=" * 60)
    print("✓ 回滚完成！")
    print(f"数据结构已恢复为 name-key，但所有卡片仍保留ID字段")
    print(f"备份文件: {BACKUP_PATH}")

if __name__ == '__main__':
    main()
