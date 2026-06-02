#!/usr/bin/env python3
"""
批量生成角色预览图（白色背景 + 角色 LoRA + 完整人物 tag）
用法: python scripts/batch_preview_gen.py [--start N] [--count N] [--dry-run]
"""

import asyncio
import json
import os
import sys
import glob
import argparse
from pathlib import Path

# ── 路径 ──
SKILL_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = SKILL_ROOT.parent
sys.path.insert(0, str(_PROJECT_ROOT))
from _env import LORA_MODEL_DIR

OUTPUT_DIR = SKILL_ROOT / "output"
PRETAGS_PATH = SKILL_ROOT / "pretags.json"
PREVIEW_DIR = SKILL_ROOT / "Tanger-Presets-Show" / "data" / "character-previews"
LORA_BASE = LORA_MODEL_DIR

sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from comfyui_client import ComfyUIClient

# ── 参数 ──
parser = argparse.ArgumentParser(description="批量生成角色预览图")
parser.add_argument("--start", type=int, default=0, help="从第几个开始")
parser.add_argument("--count", type=int, default=0, help="生成多少个(0=全部)")
parser.add_argument("--dry-run", action="store_true", help="只打印不生成")
parser.add_argument("--steps", type=int, default=20, help="采样步数")
parser.add_argument("--batch-size", type=int, default=1, help="每批提交数(队列并发)")
args = parser.parse_args()

# ── 加载 pretags ──
with open(PRETAGS_PATH, encoding="utf-8") as f:
    pretags_data = json.load(f)

chars = pretags_data.get("characters", {})

# ── 筛选有 LoRA 无预览的角色 ──
def has_preview(c):
    p = c.get("preview", "")
    return bool(p and p.strip())

candidates = []
for key, c in chars.items():
    if c.get("has_lora") and c.get("lora_file") and not has_preview(c):
        candidates.append({
            "key": key,
            "name": c.get("name", ""),
            "source": c.get("source", ""),
            "lora_file": c.get("lora_file", ""),
            "appearance": c.get("appearance", ""),
            "clothing": c.get("clothing", ""),
            "tags": c.get("tags", []),
        })

if args.dry_run:
    print(f"共 {len(candidates)} 个角色需要生成预览图")
    for c in candidates[args.start:args.start + (args.count or 10)]:
        print(f"  {c['key']} ({c['source']}) lora:{c['lora_file']}")
    sys.exit(0)

# ── 切片 ──
end = args.start + args.count if args.count else len(candidates)
batch = candidates[args.start:end]
print(f"🎯 计划生成 {len(batch)} 张预览图 ({args.start+1}-{end})")

# ── LoRA 文件查找 ──
def find_lora_path(lora_file):
    """在 ComfyUI lora 目录中查找 lora 文件"""
    # 直接搜
    direct = os.path.join(LORA_BASE, lora_file)
    if os.path.exists(direct + ".safetensors"):
        return direct + ".safetensors"
    if os.path.exists(direct):
        return direct
    # 子目录搜
    for root, dirs, files in os.walk(LORA_BASE):
        for f in files:
            if f.endswith(".safetensors"):
                name = f[:-12]
                if lora_file == name or lora_file in name or name in lora_file:
                    return os.path.join(root, f)
    return None


def build_relative_lora_path(lora_abs_path):
    """构建 ComfyUI workflow 中使用的 LoRA 名（不带后缀）"""
    lora_name = os.path.basename(lora_abs_path)
    if lora_name.endswith('.safetensors'):
        lora_name = lora_name[:-12]
    return lora_name


def build_prompt(c):
    """构建预览图 prompt"""
    lora_abs = find_lora_path(c["lora_file"])
    if not lora_abs:
        return None

    lora_rel = build_relative_lora_path(lora_abs)

    # 从 tag 中筛选出干净的描述性 tag
    tag_str = ", ".join(c["tags"])

    prompt = (
        f"masterpiece, best quality, (simple white background:1.4), "
        f"<lora:{lora_rel}:0.8:0.8>, "
        f"solo, "
        f"{tag_str}, "
        f"standing, looking at viewer, full body, "
        f"(plain white background:1.3), studio lighting"
    )
    return prompt


def get_preview_filename(c):
    """生成预览图文件名"""
    safe_key = c["key"].replace("/", "_").replace("\\", "_").replace(" ", "_")
    safe_source = (c["source"] or "unknown").replace("/", "_").replace("\\", "_").replace(" ", "_")
    return f"{safe_key}__{safe_source}.jpg"


# ── 批量生成 ──
client = ComfyUIClient(
    host="http://127.0.0.1:8188",
    output_dir=str(OUTPUT_DIR),
)


async def process_one(c):
    """生成单张预览图并更新 pretags"""
    prompt = build_prompt(c)
    if not prompt:
        print(f"  ❌ {c['key']}: LoRA 文件未找到 ({c['lora_file']})")
        return False

    try:
        saved_paths = await client.generate(
            prompt=prompt,
            negative_prompt="low quality, watermark, text, signature, bad anatomy, extra limbs",
            canvas="竖图",
            steps=args.steps,
            cfg=5.5,
            seed=-1,
            model_index=2,  # noobaiXL
            upscale=False,
        )
    except Exception as e:
        print(f"  ❌ {c['key']}: 生成失败 - {e}")
        return False

    if not saved_paths:
        print(f"  ❌ {c['key']}: 未生成图片")
        return False

    # 取面部修复后的图（最后一个 .png）
    png_paths = [p for p in saved_paths if p.suffix == ".png"]
    if not png_paths:
        print(f"  ❌ {c['key']}: 没有 .png 输出")
        return False

    face_detailered = png_paths[-1]  # 最后一张 PNG = FaceDetailer 输出

    # 转存为 JPG 到预览图目录
    preview_filename = get_preview_filename(c)
    preview_path = PREVIEW_DIR / preview_filename

    from PIL import Image
    img = Image.open(face_detailered)
    img = img.convert("RGB")
    img.save(preview_path, "JPEG", quality=85)

    # 更新 pretags.json
    preview_rel = f"./data/character-previews/{preview_filename}"

    # 重新读取确保最新
    with open(PRETAGS_PATH, encoding="utf-8") as f:
        current_data = json.load(f)

    if c["key"] in current_data.get("characters", {}):
        current_data["characters"][c["key"]]["preview"] = preview_rel
        with open(PRETAGS_PATH, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print(f"  ✅ {c['key']}: 预览图已保存 ({os.path.getsize(preview_path)} bytes)")
        return True
    else:
        print(f"  ⚠️ {c['key']}: pretags 中已不存在，跳过更新")
        return False


async def main():
    success = 0
    fail = 0
    skipped = 0

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    for i, c in enumerate(batch):
        idx = args.start + i + 1
        total = end

        # 跳过已有预览图的（可能中途手动补了）
        with open(PRETAGS_PATH, encoding="utf-8") as f:
            current_data = json.load(f)
        if c["key"] in current_data.get("characters", {}):
            existing = current_data["characters"][c["key"]]
            if existing.get("preview") and existing["preview"].strip():
                print(f"  ⏭️ [{idx}/{total}] {c['key']}: 已有预览图，跳过")
                skipped += 1
                continue

        print(f"\n🎨 [{idx}/{total}] {c['key']} ({c['source']}) lora:{c['lora_file']}")
        if await process_one(c):
            success += 1
        else:
            fail += 1

        # 每生成一张休息一下（给 ComfyUI 喘息）
        await asyncio.sleep(1)

    print(f"\n{'='*50}")
    print(f"📊 完成! 成功: {success}, 失败: {fail}, 跳过: {skipped}, 总计: {len(batch)}")


if __name__ == "__main__":
    asyncio.run(main())
