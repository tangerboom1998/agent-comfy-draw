# z-image Turbo 工作流指南

z-image Turbo 模型（Flux Turbo 架构）的配置和使用指南。

## 核心概念

- **Turbo 模型** - 4 步快速生图
- **Flux 架构** - 使用 UNETLoader + Qwen 4B CLIP
- **快速出图** - 1280×1280 约 8 秒

## 使用场景

### 场景 1: 标准生图

**推荐参数**:
- Steps: 4（Turbo 设计值）
- CFG: 1
- Resolution: 1280×1280
- Sampler: res_multistep
- Scheduler: simple

**示例**:
```bash
python comfyui_draw.py "prompt" \
  --workflow z_image_turbo.json \
  --steps 4 --cfg 1
```

### 场景 2: 环境配置

**模型文件**:
- Diffusion: `z_image_turbo_bf16.safetensors` (12GB)
- Text Encoder: `qwen_3_4b.safetensors` (8GB)
- VAE: `ae.safetensors` (335MB)

**符号链接**:
```bash
ln -sf /path/to/z_image_turbo_bf16.safetensors \
  ~/ComfyUI/models/diffusion_models/

ln -sf /path/to/qwen_3_4b.safetensors \
  ~/ComfyUI/models/text_encoders/
```

### 场景 3: 批量生图

并行提交多张图片（不同 seed）：
```bash
# 4 张并行，总耗时约 30 秒
for seed in 11111 22222 33333 44444; do
  python comfyui_draw.py "prompt" \
    --seed $seed --steps 4 &
done
wait
```

## 注意事项

- ⚠️ 需要 24GB+ VRAM（RTX 4090 或以上）
- ⚠️ Seed 最小值为 0（不是 -1）
- ⚠️ 8 步版本提升有限，推荐使用 4 步

更多警告见：[WARNINGS.md](warnings.md)

## 相关文档

- [Anima 工作流](./anima-prompt-and-workflow.md)
- [工作流节点映射](./workflow-node-mapping.md)

---

**最后更新**: 2026-06-07
