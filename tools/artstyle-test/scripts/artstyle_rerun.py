#!/usr/bin/env python3
"""
画风 LoRA 批量重跑脚本
使用正确的 <lora:filename:0.8:0.8> 格式重新生成测试图并更新描述

用法：
  python artstyle_rerun.py --start 0 --limit 15   # 处理第 0~14 条
  python artstyle_rerun.py --start 15 --limit 15   # 处理第 15~29 条
"""
import json
import os
import sys
import argparse

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..", "..")
sys.path.insert(0, _PROJECT_ROOT)
from _env import get_lora_dir, iter_lora_subdirs, detect_model_type

PRETAGS_PATH = os.path.join(_PROJECT_ROOT, "pretags.json")
DRAW_SCRIPT = os.path.join(_PROJECT_ROOT, "pretags-draw", "scripts", "comfyui_draw.py")
MODEL_DIRS = iter_lora_subdirs("画风")

# 模型文件不存在的画风，自动跳过
SKIP_MODELS = {
    "影子人": "阴影shadow.safetensors",
    "像素1": "pixel_art.safetensors",
    "像素2": "aic_pixel.safetensors",
    "doll": "joint_doll.safetensors",
}

BASE_PROMPT = "1girl, solo, long hair, blue eyes, white dress, standing, outdoors, sunlight, detailed background, cherry blossoms"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    with open(PRETAGS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    artstyles = data.get("画风", {})
    entries = list(artstyles.items())
    total = len(entries)
    subset = entries[args.start : args.start + args.limit]

    print(f"共 {total} 个 Lora=1 画风条目需要重跑")
    print(f"本次处理: {args.start + 1} ~ {args.start + len(subset)}")

    success = 0
    fail = 0
    generated = []

    for i, (name, info) in enumerate(subset):
        if name in SKIP_MODELS:
            print(f"⚠️ 跳过 {name}: 模型文件不存在")
            continue

        lora_file = info.get("模型名", "")
        if not lora_file:
            print(f"⚠️ 跳过 {name}: 无模型文件名")
            continue

        # 检查文件是否存在（遍历所有 model_type 目录）
        safepath = None
        for model_dir in MODEL_DIRS:
            candidate = os.path.join(model_dir, f"{lora_file}.safetensors")
            if os.path.exists(candidate):
                safepath = candidate
                break
        if safepath is None:
            print(f"⚠️ 跳过 {name}: 模型文件不存在 {safepath}")
            continue

        # 构建 LoRA 标签（正确格式：<lora:name:unet:clip>）
        lora_tag = f"<lora:{lora_file}:0.8:0.8>"
        prompt = f"{BASE_PROMPT}, {lora_tag}"

        print(f"\n🎨 生成: {name} ({lora_file})")
        cmd = f'cd {_PROJECT_ROOT} && python {DRAW_SCRIPT} "{prompt}" --host http://127.0.0.1:8892 --canvas 竖图 --model 2 --cfg 5.5 2>&1'

        result = os.popen(cmd).read()
        # 提取输出图片路径
        for line in result.strip().split("\n"):
            if "图片已保存" in line or "output/" in line:
                # 提取路径
                if "output/" in line:
                    path = line.split("output/")[-1].strip()
                    img_path = os.path.join(_PROJECT_ROOT, "output", path)
                    print(f"  ✅ 图片: {img_path}")
                    generated.append((name, img_path))
                    success += 1
                    break
        else:
            # 尝试从输出中找 PNG 文件
            for line in result.strip().split("\n"):
                if ".png" in line and "CCUI_" in line:
                    import re
                    match = re.search(r'(CCUI_[a-f0-9]+_0\.png)', line)
                    if match:
                        img_path = os.path.join(_PROJECT_ROOT, "output", match.group(1))
                        print(f"  ✅ 图片: {img_path}")
                        generated.append((name, img_path))
                        success += 1
                        break
            else:
                print(f"  ❌ 生成失败")
                fail += 1

    print(f"\n完成! 成功: {success}, 失败: {fail}")
    if generated:
        print("\n成功生成的图片:")
        for name, path in generated:
            print(f"  {name}|{path}")


if __name__ == "__main__":
    main()
