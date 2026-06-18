"""测试 anima 工作流"""
import json
import os
import random
import sys
import time
import uuid
from pathlib import Path

# 加载 .env
_SKILL_ROOT = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _SKILL_ROOT.parent
sys.path.insert(0, str(_PROJECT_ROOT))
import _env  # noqa: F401 — 触发 .env 加载

import requests
import websocket

COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188")
WS_HOST = COMFYUI_HOST.replace("http://", "ws://").replace("https://", "wss://")
WORKFLOW_PATH = _SKILL_ROOT / "assets" / "anima_api_workflow.json"
OUTPUT_DIR = Path(os.environ.get("COMFYUI_OUTPUT_DIR", "output"))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 加载工作流模板
with open(WORKFLOW_PATH) as f:
    workflow = json.load(f)

# 替换 prompt
seed = random.randint(1, 2**31)
workflow["4"]["inputs"]["seed"] = seed
workflow["10"]["inputs"]["input"] = (
    "masterpiece, score_7, painterly, best quality, "
    "1girl, white hair, fox ears, yellow eyes, "
    "wearing red cheongsam, bare shoulders, skin exposure, "
    "sitting on wooden floor, looking at viewer, "
    "elegant, seductive, intricate details, "
    "dark background, soft lighting, cinematic"
)

# 替换负prompt
workflow["37"]["inputs"]["text"] = (
    "lowres, bad, error, fewer, extra, missing, worst quality, "
    "jpeg artifacts, low quality, watermark, unfinished, displeasing, "
    "oldest, faceless, bad background, furry, extra arms, extra fingers, "
    "extra legs, extra toes, blush, more than 5 fingers, head_tilt"
)

print(f"种子: {seed}")
print(f"尺寸: {workflow['1']['inputs']['width']}x{workflow['1']['inputs']['height']}")
print(f"步数: {workflow['30']['inputs']['steps']} (主) + {workflow['50']['inputs']['steps']} (面部)")
print(f"CFG: {workflow['30']['inputs']['cfg']} (主) + {workflow['50']['inputs']['cfg']} (面部)")
print(f"模型: {workflow['25']['inputs']['unet_name']}")

# ── 提交工作流 ──
client_id = str(uuid.uuid4())

# 先获取队列
r = requests.post(
    f"{COMFYUI_HOST}/prompt",
    json={"prompt": workflow, "client_id": client_id},
    timeout=30,
)
if r.status_code != 200:
    print(f"❌ 提交失败: {r.status_code}")
    print(r.text)
    sys.exit(1)

resp = r.json()
prompt_id = resp["prompt_id"]
print(f"✅ 已提交, prompt_id: {prompt_id}")
print(f"   队列中任务数: {resp.get('number', '?')}")

# ── 监听 WebSocket 等待完成 ──
ws_url = f"{WS_HOST}/ws?clientId={client_id}"
ws = websocket.create_connection(ws_url, timeout=300)

print("⏳ 等待生成...")
output_images = []

try:
    while True:
        msg = ws.recv()
        if isinstance(msg, str):
            data = json.loads(msg)
            msg_type = data.get("type")
            if msg_type == "executing":
                node = data.get("data", {}).get("node")
                if node is None:
                    print("✅ 生成完成!")
                    break
                else:
                    progress_nodes = {str(k) for k in [
                        30,  # KSamplerAdvanced
                        50,  # FaceDetailer
                    ]}
                    if node in progress_nodes:
                        pass  # 正在采样/面部修复
            elif msg_type == "execution_cached":
                pass
            elif msg_type == "progress":
                pass
        elif isinstance(msg, bytes):
            # 二进制消息 - 图片数据
            output_images.append(msg)
except Exception as e:
    print(f"⚠️ WebSocket 错误: {e}")

ws.close()

# ── 获取输出 ──
r = requests.get(f"{COMFYUI_HOST}/history/{prompt_id}", timeout=10)
if r.status_code == 200:
    history = r.json()
    node_outputs = history.get(prompt_id, {}).get("outputs", {})
    print(f"\n📂 输出节点:")
    for node_id, node_data in node_outputs.items():
        print(f"   节点 {node_id}: {list(node_data.keys())}")
        if "images" in node_data:
            for img in node_data["images"]:
                print(f"     - {img.get('filename')} ({img.get('type')})")
                # 下载图片
                img_url = f"{COMFYUI_HOST}/view?filename={img['filename']}&subfolder={img.get('subfolder','')}&type={img['type']}"
                img_r = requests.get(img_url, timeout=30)
                if img_r.status_code == 200:
                    ext = img_r.headers.get('Content-Type', '').split('/')[-1]
                    if ext == 'jpeg':
                        ext = 'jpg'
                    out_path = OUTPUT_DIR / f"anima_test_{prompt_id[:8]}.{ext}"
                    with open(out_path, "wb") as f:
                        f.write(img_r.content)
                    print(f"     ✅ 已保存: {out_path}")
else:
    print(f"❌ 获取历史失败: {r.status_code}")

print("\n✅ 测试完成")
