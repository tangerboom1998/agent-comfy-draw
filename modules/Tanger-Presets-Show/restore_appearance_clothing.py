#!/usr/bin/env python3
"""
从 pre_tag_c_info.xlsx 恢复人物卡片的 appearance 和 clothing 字段
根据 cname + source 匹配
"""
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path

EXCEL_PATH = '../pre_tag_c_info.xlsx'

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

def main():
    print("=" * 60)
    print("恢复 appearance 和 clothing 字段")
    print("=" * 60)
    
    # 读取Excel文件
    print(f"\n读取Excel文件: {EXCEL_PATH}")
    try:
        df = pd.read_excel(EXCEL_PATH)
        print(f"✓ Excel文件读取成功，共 {len(df)} 行")
        print(f"  列名: {list(df.columns)}")
    except Exception as e:
        print(f"错误: 读取Excel失败 - {e}")
        return
    
    # 读取pretags.json
    print(f"\n读取数据文件: {DATA_PATH}")
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✓ 数据文件读取成功")
    except Exception as e:
        print(f"错误: 读取数据文件失败 - {e}")
        return
    
    # 创建备份
    backup_path = str(Path(DATA_PATH).parent / f'pretags_backup_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    print(f"\n创建备份: {backup_path}")
    try:
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 备份创建成功")
    except Exception as e:
        print(f"错误: 创建备份失败 - {e}")
        return
    
    # 构建Excel数据的查找字典 (cname, source) -> (appearance, clothing)
    print("\n构建Excel数据索引...")
    excel_map = {}
    for _, row in df.iterrows():
        cname = str(row.get('cname', '')).strip()
        source = str(row.get('source', '')).strip()
        appearance = str(row.get('appearance', '')).strip()
        clothing = str(row.get('clothing', '')).strip()
        
        # 处理NaN值
        if appearance == 'nan':
            appearance = ''
        if clothing == 'nan':
            clothing = ''
        
        key = (cname, source)
        excel_map[key] = (appearance, clothing)
    
    print(f"✓ Excel索引构建完成，共 {len(excel_map)} 条记录")
    
    # 遍历pretags.json中的人物卡片，匹配并填充字段（只更新有lora的卡片）
    print("\n开始匹配和填充字段（只更新has_lora=True的卡片）...")
    characters = data.get('characters', {})
    matched_count = 0
    updated_count = 0
    missing_count = 0
    skipped_no_lora = 0
    
    for char_id, char_data in characters.items():
        # 只处理有lora的卡片
        if not char_data.get('has_lora', False):
            skipped_no_lora += 1
            continue
            
        cname = char_data.get('cname', '').strip()
        source = char_data.get('source', '').strip()
        key = (cname, source)
        
        if key in excel_map:
            matched_count += 1
            appearance, clothing = excel_map[key]
            
            # 更新字段
            char_data['appearance'] = appearance
            char_data['clothing'] = clothing
            
            # 更新tags字段：保持数组格式，从appearance和clothing提取
            tag_list = []
            if appearance:
                tag_list.extend([t.strip() for t in appearance.split(',') if t.strip()])
            if clothing:
                tag_list.extend([t.strip() for t in clothing.split(',') if t.strip()])
            
            # 去重
            unique_tags = list(dict.fromkeys(tag_list))  # 保持顺序的去重
            char_data['tags'] = unique_tags
            char_data['tags_count'] = len(unique_tags)
            
            updated_count += 1
        else:
            missing_count += 1
            if missing_count <= 10:  # 只显示前10个未匹配的
                print(f"  未匹配: cname='{cname}', source='{source}'")
    
    print(f"\n匹配统计:")
    print(f"  总卡片数: {len(characters)}")
    print(f"  有lora卡片: {len(characters) - skipped_no_lora}")
    print(f"  无lora卡片（已跳过）: {skipped_no_lora}")
    print(f"  成功匹配: {matched_count}")
    print(f"  已更新: {updated_count}")
    print(f"  未匹配: {missing_count}")
    
    # 写入更新后的数据
    print(f"\n写入更新后的数据到: {DATA_PATH}")
    try:
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 数据写入成功")
    except Exception as e:
        print(f"错误: 写入文件失败 - {e}")
        return
    
    print("\n" + "=" * 60)
    print("✓ 恢复完成！")
    print(f"备份文件位于: {backup_path}")
    print("=" * 60)

if __name__ == '__main__':
    main()
