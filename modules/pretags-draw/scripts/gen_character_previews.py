#!/usr/bin/env python3
"""
人物 LoRA 预览图批量生成脚本

功能：
1. 扫描 pretags 中所有带 lora 的人物
2. 检查是否已有预览图
3. 对没有预览图的人物，使用立绘模板生成
4. 保存为预览图并更新 pretags.json

用法：
    python scripts/gen_character_previews.py                    # 生成全部缺失的
    python scripts/gen_character_previews.py --limit 10         # 只生成 10 个
    python scripts/gen_character_previews.py --check            # 只检查，不生成
    python scripts/gen_character_previews.py --name 弗洛洛       # 只生成指定角色

立绘模板：
    masterpiece, best quality, ultra-detailed, very aesthetic, absurdres,
    <lora:{lora_file}:{unet_weight}:{clip_weight}>,
    solo, {name}, {tags},
    full body, standing, white background, simple background,
    detailed face, beautiful eyes, looking at viewer
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ── 路径配置 ──────────────────────────────────────────────────────────────
SKILL_ROOT = Path(__file__).resolve().parent.parent
PRETAGS_PATH = SKILL_ROOT / "pretags.json"
PREVIEW_DIR = SKILL_ROOT / "Tanger-Presets-Show" / "data" / "character-previews"
OUTPUT_DIR = SKILL_ROOT / "output"
COMFYUI_DRAW = SKILL_ROOT / "scripts" / "comfyui_draw.py"

# ── 立绘模板 ──────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = "masterpiece, best quality, ultra-detailed, very aesthetic, absurdres, <lora:{lora_file}:{unet_weight}:{clip_weight}>, solo, {name}, {tags}, full body, standing, white background, simple background, detailed face, beautiful eyes, looking at viewer"

# ── 默认参数 ──────────────────────────────────────────────────────────────
DEFAULT_STEPS = 28
DEFAULT_CFG = 5.5
DEFAULT_CANVAS = "竖图"


def load_pretags():
    """加载 pretags.json"""
    with open(PRETAGS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_pretags(data):
    """保存 pretags.json"""
    with open(PRETAGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_lora_characters(data):
    """获取所有带 lora 的人物"""
    chars = data.get('characters', {})
    return {k: v for k, v in chars.items()
            if isinstance(v, dict) and v.get('has_lora') and v.get('lora_file')}


def safe_filename(name):
    """清理文件名中的特殊字符"""
    return name.replace('/', '_').replace('\\', '_').replace(':', '_')


def has_preview(cname, source):
    """检查预览图是否存在"""
    safe_cname = safe_filename(cname)
    safe_source = safe_filename(source)
    preview_path = PREVIEW_DIR / f"{safe_cname}__{safe_source}.jpg"
    return preview_path.exists()


def build_prompt(char_info):
    """根据角色信息构建 prompt"""
    lora_file = char_info.get('lora_file', '')
    unet_weight = char_info.get('unet_weight', 0.8)
    clip_weight = char_info.get('clip_weight', 0.8)
    name = char_info.get('name', '')
    tags = char_info.get('tags', [])
    
    # 处理 tags：去除空值，逗号拼接
    tags_str = ', '.join([t.strip() for t in tags if t.strip()])
    
    prompt = PROMPT_TEMPLATE.format(
        lora_file=lora_file,
        unet_weight=unet_weight,
        clip_weight=clip_weight,
        name=name,
        tags=tags_str
    )
    
    # 清理多余空白和换行
    prompt = ' '.join(prompt.split())
    return prompt


def generate_image(prompt):
    """调用 comfyui_draw.py 生成图片"""
    cmd = [
        sys.executable,
        str(COMFYUI_DRAW),
        prompt,
        "--steps", str(DEFAULT_STEPS),
        "--cfg", str(DEFAULT_CFG),
        "--canvas", DEFAULT_CANVAS
    ]
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,  # 2 分钟超时
        cwd=str(SKILL_ROOT)
    )
    
    if result.returncode != 0:
        return None, result.stderr
    
    # 解析输出，找到生成的文件路径
    output = result.stdout
    for line in output.split('\n'):
        if '图片已保存:' in line and '_1.png' in line:
            path = line.split('图片已保存:')[-1].strip()
            if os.path.exists(path):
                return path, None
    
    # 如果没找到 _1.png，尝试查找最新的文件
    files = sorted(OUTPUT_DIR.glob("CCUI_*_1.png"), key=os.path.getmtime, reverse=True)
    if files:
        return str(files[0]), None
    
    return None, "未找到生成的图片"


def save_preview(src_png, cname, source):
    """保存预览图（转换为 jpg）"""
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: PIL/Pillow not installed. Try: pip install Pillow")
        sys.exit(1)
    
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    
    safe_cname = safe_filename(cname)
    safe_source = safe_filename(source)
    dst_jpg = PREVIEW_DIR / f"{safe_cname}__{safe_source}.jpg"
    
    img = Image.open(src_png).convert('RGB')
    img.save(str(dst_jpg), 'JPEG', quality=85)
    
    return str(dst_jpg)


def update_preview_field(data, key, preview_path):
    """更新 pretags 中的 preview 字段"""
    if key in data['characters']:
        rel_path = f"./data/character-previews/{Path(preview_path).name}"
        data['characters'][key]['preview'] = rel_path
        return True
    return False


def check_missing_previews(data, name_filter=None):
    """检查缺失预览图的角色"""
    lora_chars = get_lora_characters(data)
    missing = []
    
    for key, info in lora_chars.items():
        cname = info.get('cname', key)
        source = info.get('source', '')
        
        if name_filter and name_filter not in cname:
            continue
        
        if not has_preview(cname, source):
            missing.append((key, cname, source, info))
    
    return missing


def main():
    global DEFAULT_STEPS, DEFAULT_CFG
    
    parser = argparse.ArgumentParser(description="人物 LoRA 预览图批量生成")
    parser.add_argument("--check", action="store_true", help="只检查缺失的预览图，不生成")
    parser.add_argument("--name", type=str, help="只处理指定角色名（模糊匹配）")
    parser.add_argument("--limit", type=int, default=0, help="最多生成几个（0=不限）")
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS, help="采样步数")
    parser.add_argument("--cfg", type=float, default=DEFAULT_CFG, help="CFG 值")
    args = parser.parse_args()
    
    # 更新参数
    DEFAULT_STEPS = args.steps
    DEFAULT_CFG = args.cfg
    
    # 加载 pretags
    print(f"加载 pretags: {PRETAGS_PATH}")
    data = load_pretags()
    lora_chars = get_lora_characters(data)
    print(f"总人物: {len(data.get('characters', {}))}, 带 lora: {len(lora_chars)}")
    
    # 检查缺失的预览图
    missing = check_missing_previews(data, args.name)
    print(f"缺失预览图: {len(missing)}")
    
    if args.check:
        print("\n缺失预览图的角色:")
        for key, cname, source, info in missing[:20]:
            lora = info.get('lora_file', '')
            print(f"  - {cname} ({source}) | lora: {lora}")
        if len(missing) > 20:
            print(f"  ... 还有 {len(missing) - 20} 个")
        return
    
    if not missing:
        print("\n所有带 lora 的角色都有预览图！")
        return
    
    # 限制数量
    if args.limit > 0:
        missing = missing[:args.limit]
    
    print(f"\n开始生成 {len(missing)} 个预览图...")
    
    success_count = 0
    fail_count = 0
    
    for i, (key, cname, source, info) in enumerate(missing, 1):
        lora_file = info.get('lora_file', '')
        
        print(f"\n[{i}/{len(missing)}] {cname} ({source})")
        print(f"  LoRA: {lora_file}")
        
        # 构建 prompt
        prompt = build_prompt(info)
        print(f"  Prompt: {prompt[:80]}...")
        
        # 生成图片
        img_path, error = generate_image(prompt)
        
        if error:
            print(f"  生成失败: {error}")
            fail_count += 1
            continue
        
        print(f"  图片生成: {img_path}")
        
        # 保存预览图
        preview_path = save_preview(img_path, cname, source)
        print(f"  预览图保存: {preview_path}")
        
        # 更新 pretags
        update_preview_field(data, key, preview_path)
        save_pretags(data)
        print(f"  pretags 已更新")
        
        success_count += 1
        
        # 清理临时文件
        try:
            os.remove(img_path)
        except:
            pass
        
        # 短暂延迟，避免 API 过载
        if i < len(missing):
            time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"完成率: {success_count}/{len(missing)} ({100*success_count/max(1,len(missing)):.1f}%)")
    
    print(f"\n请重启 server 使预览图生效")


if __name__ == "__main__":
    main()
