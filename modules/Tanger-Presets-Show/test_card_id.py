#!/usr/bin/env python3
"""测试卡片ID生成功能"""
import json
import hashlib

def generate_card_id(card_type, **fields):
    """生成卡片ID（8位hash）"""
    if card_type == 'character':
        text = f"{fields.get('cname', '')}{fields.get('name', '')}{fields.get('source', '')}"
    else:
        text = f"{fields.get('name', '')}{fields.get('tag', '')}"
    
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:8]

# 测试人物卡片ID生成
print("=== 测试人物卡片ID生成 ===")
char1_id = generate_card_id('character', cname='测试角色', name='test_character', source='测试来源')
print(f"角色1 ID: {char1_id}")
print(f"  cname='测试角色', name='test_character', source='测试来源'")

char2_id = generate_card_id('character', cname='测试角色', name='test_character', source='另一个来源')
print(f"\n角色2 ID: {char2_id}")
print(f"  cname='测试角色', name='test_character', source='另一个来源'")
print(f"  不同来源 -> 不同ID: {char1_id != char2_id}")

char3_id = generate_card_id('character', cname='测试角色', name='test_character', source='测试来源')
print(f"\n角色3 ID: {char3_id}")
print(f"  cname='测试角色', name='test_character', source='测试来源'")
print(f"  相同字段 -> 相同ID: {char1_id == char3_id}")

# 测试标签卡片ID生成
print("\n=== 测试标签卡片ID生成 ===")
tag1_id = generate_card_id('tag', name='画风标签', tag='anime style')
print(f"标签1 ID: {tag1_id}")
print(f"  name='画风标签', tag='anime style'")

tag2_id = generate_card_id('tag', name='画风标签', tag='realistic')
print(f"\n标签2 ID: {tag2_id}")
print(f"  name='画风标签', tag='realistic'")
print(f"  不同tag -> 不同ID: {tag1_id != tag2_id}")

tag3_id = generate_card_id('tag', name='画风标签', tag='anime style')
print(f"\n标签3 ID: {tag3_id}")
print(f"  name='画风标签', tag='anime style'")
print(f"  相同字段 -> 相同ID: {tag1_id == tag3_id}")

# 读取实际数据文件，检查现有卡片
print("\n=== 检查现有数据文件 ===")
try:
    with open('data/pretags.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查人物卡片
    characters = data.get('characters', {})
    char_count = len(characters)
    char_with_id = sum(1 for c in characters.values() if 'id' in c)
    print(f"人物卡片总数: {char_count}")
    print(f"已有ID的卡片: {char_with_id}")
    print(f"缺少ID的卡片: {char_count - char_with_id}")
    
    # 显示前3个人物卡片的ID情况
    print("\n前3个人物卡片示例:")
    for i, (cname, char) in enumerate(list(characters.items())[:3]):
        has_id = 'id' in char
        if has_id:
            print(f"  {i+1}. {cname}: ID={char['id']}")
        else:
            expected_id = generate_card_id('character',
                cname=char.get('cname', ''),
                name=char.get('name', ''),
                source=char.get('source', ''))
            print(f"  {i+1}. {cname}: 无ID (应为 {expected_id})")
    
    # 检查标签卡片
    categories = data.get('categories', {})
    tag_count = 0
    tag_with_id = 0
    for cat_name, tags in categories.items():
        tag_count += len(tags)
        tag_with_id += sum(1 for t in tags.values() if 'id' in t)
    
    print(f"\n标签卡片总数: {tag_count}")
    print(f"已有ID的标签: {tag_with_id}")
    print(f"缺少ID的标签: {tag_count - tag_with_id}")
    
    # 显示第一个分类的前3个标签
    if categories:
        first_cat = list(categories.keys())[0]
        print(f"\n'{first_cat}' 分类前3个标签示例:")
        for i, (tag_name, tag) in enumerate(list(categories[first_cat].items())[:3]):
            has_id = 'id' in tag
            if has_id:
                print(f"  {i+1}. {tag_name}: ID={tag['id']}")
            else:
                expected_id = generate_card_id('tag',
                    name=tag.get('name', ''),
                    tag=tag.get('tag', ''))
                print(f"  {i+1}. {tag_name}: 无ID (应为 {expected_id})")

except FileNotFoundError:
    print("数据文件不存在: data/pretags.json")
except Exception as e:
    print(f"读取数据文件出错: {e}")

print("\n=== 测试完成 ===")
