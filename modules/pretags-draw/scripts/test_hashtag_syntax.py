#!/usr/bin/env python3
"""测试新的 # 前缀语法"""

import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from tag_producer import TagProducer, Settings

def test_hashtag_syntax():
    """测试 # 前缀语法"""
    
    # 初始化
    settings = Settings(sys='comfyui')
    producer = TagProducer(settings)
    
    # 测试用例
    test_cases = [
        # 基础人物指令
        ("#人物 瓦斯弹 外貌", "测试人物+外貌"),
        ("#人物 瓦斯弹 外貌 服装", "测试人物+外貌+服装"),
        
        # 直接角色名（简写）
        ("#瓦斯弹", "测试直接角色名"),
        
        # 画风指令
        ("#画风 赛璐璐", "测试画风标签"),
        
        # 撸串指令
        ("#撸串 3", "测试画师随机"),
        
        # 随机角色
        ("#随机 口袋妖怪", "测试随机角色"),
        
        # 混合使用
        ("#人物 瓦斯弹 外貌,#画风 赛璐璐,#撸串 2", "测试混合指令"),
        
        # 英文+中文混合
        ("1girl, #瓦斯弹, masterpiece, #画风 赛璐璐", "测试英文中文混合"),
        
        # 未匹配的 # 命令（应保留原样）
        ("#未知命令 测试", "测试未知命令"),
    ]
    
    print("=" * 80)
    print("测试新的 # 前缀语法")
    print("=" * 80)
    
    for i, (input_prompt, description) in enumerate(test_cases, 1):
        print(f"\n[测试 {i}] {description}")
        print(f"输入: {input_prompt}")
        try:
            output = producer.tagrep(input_prompt)
            print(f"输出: {output}")
        except Exception as e:
            print(f"错误: {e}")
        print("-" * 80)
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    test_hashtag_syntax()
