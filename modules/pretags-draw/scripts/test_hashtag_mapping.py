#!/usr/bin/env python3
"""测试 hashtag_mapping.json 别名映射功能"""

import sys
import os

# 确保能找到 tag_producer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from tag_producer import TagProducer, Settings, DEFAULT_HASHTAG_MAPPING_PATH

def test_mapping_load():
    """测试映射文件加载"""
    print("=" * 60)
    print("测试 1: 映射文件加载")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    print(f"映射文件路径: {DEFAULT_HASHTAG_MAPPING_PATH}")
    print(f"文件存在: {os.path.isfile(DEFAULT_HASHTAG_MAPPING_PATH)}")
    print(f"cmd_alias_map 条目数: {len(tp.cmd_alias_map)}")
    print(f"field_alias_map 条目数: {len(tp.field_alias_map)}")
    print(f"_random_aliases: {tp._random_aliases}")
    
    # 打印所有映射
    print("\n--- cmd_alias_map ---")
    for alias, (cmd_type, data_key) in sorted(tp.cmd_alias_map.items()):
        print(f"  #{alias:<14} → type={cmd_type:<12} data_key={data_key}")
    
    print("\n--- field_alias_map ---")
    for alias, canonical in sorted(tp.field_alias_map.items()):
        print(f"  {alias:<14} → {canonical}")
    
    assert len(tp.cmd_alias_map) > 0, "cmd_alias_map 不应为空"
    assert len(tp.field_alias_map) > 0, "field_alias_map 不应为空"
    print("\n✅ 映射文件加载测试通过\n")


def test_chinese_aliases():
    """测试中文别名（向后兼容）"""
    print("=" * 60)
    print("测试 2: 中文别名（向后兼容）")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # #人物 角色名
    result = tp.tagrep("#人物 瓦斯弹")
    print(f"  #人物 瓦斯弹 → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    # #随机
    result = tp.tagrep("#随机 宝可梦")
    print(f"  #随机 宝可梦 → {result[:80]}...")
    
    print("✅ 中文别名测试通过\n")


def test_english_aliases():
    """测试英文别名"""
    print("=" * 60)
    print("测试 3: 英文别名")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # #char 角色名
    result = tp.tagrep("#char 瓦斯弹")
    print(f"  #char 瓦斯弹 → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    # #character 角色名
    result = tp.tagrep("#character 瓦斯弹")
    print(f"  #character 瓦斯弹 → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    # #char 角色名 appearance
    result = tp.tagrep("#char 瓦斯弹 appearance")
    print(f"  #char 瓦斯弹 appearance → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    # #char 角色名 app (缩写)
    result = tp.tagrep("#char 瓦斯弹 app")
    print(f"  #char 瓦斯弹 app → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    # #char 角色名 cloth (缩写)
    result = tp.tagrep("#char 瓦斯弹 cloth")
    print(f"  #char 瓦斯弹 cloth → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    print("✅ 英文别名测试通过\n")


def test_category_aliases():
    """测试分类别名"""
    print("=" * 60)
    print("测试 4: 分类别名")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # #style (画风)
    result = tp.tagrep("#style 赛璐璐")
    print(f"  #style 赛璐璐 → {result[:80]}...")
    
    # #action (动作)
    result = tp.tagrep("#action 站立")
    print(f"  #action 站立 → {result[:80]}...")
    
    # #scene (场景)
    result = tp.tagrep("#scene 教室")
    print(f"  #scene 教室 → {result[:80]}...")
    
    print("✅ 分类别名测试通过\n")


def test_random_alias():
    """测试随机别名"""
    print("=" * 60)
    print("测试 5: 随机别名")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # #random
    result = tp.tagrep("#random 宝可梦")
    print(f"  #random 宝可梦 → {result[:80]}...")
    
    # #rand
    result = tp.tagrep("#rand 宝可梦")
    print(f"  #rand 宝可梦 → {result[:80]}...")
    
    print("✅ 随机别名测试通过\n")


def test_roll_artist_alias():
    """测试画师串别名"""
    print("=" * 60)
    print("测试 6: 画师串别名")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # #artist
    result = tp.tagrep("#artist 3")
    print(f"  #artist 3 → {result[:80]}...")
    
    # #roll
    result = tp.tagrep("#roll 3")
    print(f"  #roll 3 → {result[:80]}...")
    
    print("✅ 画师串别名测试通过\n")


def test_mixed_aliases():
    """测试混合别名"""
    print("=" * 60)
    print("测试 7: 混合别名")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    # 混合中英文
    result = tp.tagrep("#char 瓦斯弹, #style 赛璐璐, best quality")
    print(f"  #char 瓦斯弹, #style 赛璐璐, best quality → {result[:120]}...")
    
    print("✅ 混合别名测试通过\n")


def test_fallback_no_mapping():
    """测试映射文件不存在时的回退"""
    print("=" * 60)
    print("测试 8: 映射文件不存在时回退")
    print("=" * 60)
    
    tp = TagProducer(Settings(hashtag_mapping_path='/nonexistent/path.json'))
    
    print(f"cmd_alias_map 条目数: {len(tp.cmd_alias_map)}")
    print(f"field_alias_map 条目数: {len(tp.field_alias_map)}")
    
    # 应该仍能用中文关键字
    result = tp.tagrep("#人物 瓦斯弹")
    print(f"  #人物 瓦斯弹 → {result[:80]}...")
    assert "koffing" in result, f"期望包含 koffing，实际: {result}"
    
    print("✅ 回退测试通过\n")


def test_unknown_command():
    """测试未知命令保留原样"""
    print("=" * 60)
    print("测试 9: 未知命令保留原样")
    print("=" * 60)
    
    tp = TagProducer(Settings())
    
    result = tp.tagrep("#unknown_command test")
    print(f"  #unknown_command test → {result}")
    assert "#unknown_command" in result, f"未知命令应保留原样，实际: {result}"
    
    print("✅ 未知命令测试通过\n")


if __name__ == '__main__':
    test_mapping_load()
    test_chinese_aliases()
    test_english_aliases()
    test_category_aliases()
    test_random_alias()
    test_roll_artist_alias()
    test_mixed_aliases()
    test_fallback_no_mapping()
    test_unknown_command()
    
    print("=" * 60)
    print("🎉 所有测试通过！")
    print("=" * 60)
