#!/usr/bin/env python3
"""
画风测试工作流 — 多维（人、景、人+景）生图 → 看图描述 → 补充画风描述

用法：
  python artstyle_test.py [画风名称1] [画风名称2] ...
  不传参则自动选取前5个有LoRA且tag非空的画风进行测试

流程：
  1. 对每个画风生成3张测试图（人物/场景/人物+场景）
  2. 用 vision 模型分析每张图的画风特征
  3. 综合分析结果，生成画风描述写入 pretags.json
"""

import json
import os
import sys
import subprocess
import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PRETAGS_PATH = SKILL_DIR.parent / "pretags.json"
OUTPUT_DIR = SKILL_DIR / "output" / "artstyle_test"
COMFYUI_SCRIPT = SKILL_DIR / "scripts" / "comfyui_draw.py"

# 测试用提示词模板
TEST_PROMPTS = {
    "人物": "masterpiece, best quality, 1girl, solo, white hair, yellow eyes, simple background, portrait",
    "场景": "masterpiece, best quality, landscape, mountains, sunset, clouds, nature, scenery, no humans",
    "人物+场景": "masterpiece, best quality, 1girl, white hair, yellow eyes, standing, mountains, sunset, landscape, nature",
}

def load_pretags():
    with open(PRETAGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_pretags(data):
    with open(PRETAGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_test_styles(data, limit=5, style_names=None):
    """获取待测试的画风列表"""
    if style_names:
        return [(name, data['style'][name]) for name in style_names if name in data['style']]
    
    candidates = []
    for cname, v in data['style'].items():
        if v.get('Lora') == 1 and v.get('tag') and v['tag'].strip() and v['tag'].strip() != ',':
            candidates.append((cname, v))
    return candidates[:limit]

def build_prompt(style_entry, test_type):
    """构建带画风tag的测试提示词"""
    base = TEST_PROMPTS[test_type]
    style_tag = style_entry.get('tag', '').strip().rstrip(',')
    
    # 如果画风有LoRA，加上LoRA调用
    if style_entry.get('Lora') == 1:
        model_name = style_entry.get('model file name', '')
        unet = style_entry.get('unet weight', 0.8)
        clip = style_entry.get('clip weight', 0.8)
        lora_tag = f"<lora:{model_name}:{unet}:{clip}>"
        return f"{lora_tag}, {style_tag}, {base}"
    else:
        return f"{style_tag}, {base}"

def generate_image(prompt, output_name):
    """调用 comfyui_draw 生成图片"""
    output_path = OUTPUT_DIR / f"{output_name}.png"
    cmd = [
        sys.executable, str(COMFYUI_SCRIPT),
        prompt,
        "--canvas", "方图",
        "--model", "2",
        "--steps", "28",
        "--cfg", "7.0",
    ]
    
    print(f"  生成中: {output_name}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    
    # 从输出中找到图片路径
    for line in result.stdout.split('\n'):
        if '图片已保存' in line and '.png' in line:
            # 提取路径
            match = re.search(r'(output/\S+\.png)', line)
            if match:
                src = SKILL_DIR / match.group(1)
                if src.exists():
                    # 移动到测试目录
                    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                    import shutil
                    shutil.copy2(src, output_path)
                    return output_path
    return None

def analyze_image(image_path, style_name, test_type):
    """用vision分析图片画风特征（返回分析文本）"""
    # 这个函数需要在agent环境中调用vision_analyze工具
    # 在脚本中我们返回一个占位符，实际由agent调用
    return f"[待分析] {style_name} - {test_type}: {image_path}"

def run_test(style_names=None, limit=5):
    """执行画风测试流程"""
    data = load_pretags()
    styles = get_test_styles(data, limit=limit, style_names=style_names)
    
    if not styles:
        print("没有找到可测试的画风")
        return
    
    print(f"=== 画风测试 ===")
    print(f"待测试画风: {len(styles)} 个")
    print(f"每个画风生成: 3 张测试图")
    print()
    
    results = {}
    
    for style_name, style_entry in styles:
        print(f"▶ 画风: {style_name}")
        style_results = {}
        
        for test_type in ["人物", "场景", "人物+场景"]:
            prompt = build_prompt(style_entry, test_type)
            safe_name = re.sub(r'[^\w]', '_', style_name)
            output_name = f"{safe_name}_{test_type}"
            
            image_path = generate_image(prompt, output_name)
            if image_path:
                style_results[test_type] = str(image_path)
                print(f"    ✅ {test_type}: {image_path}")
            else:
                print(f"    ❌ {test_type}: 生成失败")
        
        results[style_name] = style_results
        print()
    
    # 保存结果供agent后续分析
    results_path = OUTPUT_DIR / "test_results.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"测试结果已保存: {results_path}")
    print(f"请使用 vision_analyze 工具分析各图片，然后更新画风描述")
    
    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='画风测试工作流')
    parser.add_argument('styles', nargs='*', help='指定测试的画风名称')
    parser.add_argument('--limit', type=int, default=5, help='测试画风数量（默认5）')
    args = parser.parse_args()
    
    run_test(style_names=args.styles if args.styles else None, limit=args.limit)
