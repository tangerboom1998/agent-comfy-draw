# z-image Turbo 工作流指南

> 合并自: z-image-turbo-workflow.md, z-image-lora-catalog.md, z-image-proven-configs.md

---

## 一、首次配置

### 环境要求
- ComfyUI v0.19.1+, PyTorch 2.9.0+cu128, Python 3.11+
- GPU: RTX 4090 (24GB VRAM) 或以上
- ComfyUI 启动耗时约 2-3 分钟（含 ComfyRegistry 数据拉取）

### 模型文件

| 模型 | 文件 | 大小 |
|------|------|------|
| Diffusion | `z_image_turbo_bf16.safetensors` | 12GB |
| Text Encoder | `qwen_3_4b.safetensors` | 8GB |
| VAE | `ae.safetensors` | 335MB |

### Symlinks

```bash
# diffusion model
ln -sf /opt/comfyui/save/models/unet/z_image_turbo_bf16.safetensors \
  ~/lr/ComfyUI/models/diffusion_models/z_image_turbo_bf16.safetensors

# text encoder (from qwen/ subdirectory to root)
ln -sf ~/lr/ComfyUI/models/text_encoders/qwen/qwen_3_4b.safetensors \
  ~/lr/ComfyUI/models/text_encoders/qwen_3_4b.safetensors
```

---

## 二、生图参数

### 默认参数

| 参数 | 值 |
|------|-----|
| Steps | 4 (turbo 模型设计为 4 步出图) |
| CFG | 1 |
| Resolution | 1280×1280（可调） |
| Sampler | res_multistep |
| Scheduler | simple |
| Shift | 3 |
| Seed | 0 (random, min=0 not -1) |

### 4步 vs 8步

8步版本在细节纹理上略优于4步，但差异不大（turbo 模型本身设计为 4 步出图）。

### 并行生图

4 张并行提交（seed=11111/22222/33333/44444），1280×1280, steps=8, CFG=1：
- 总耗时约 30 秒完成全部 4 张（ComfyUI 内部串行执行，但提交是异步的）

---

## 三、工作流节点结构

| Node ID | Class | 功能 |
|---------|-------|------|
| 30 | CLIPLoader | 加载 qwen_3_4b, type=lumina2 |
| 29 | VAELoader | 加载 ae.safetensors |
| 28 | UNETLoader | 加载 z_image_turbo_bf16 |
| 27 | CLIPTextEncode | 编码 prompt → conditioning |
| 33 | ConditioningZeroOut | positive → negative (零化) |
| 13 | EmptySD3LatentImage | 创建空白 latent |
| 11 | ModelSamplingAuraFlow | 调整采样 shift=3 |
| 3 | KSampler | 采样 |
| 8 | VAEDecode | latent → image |
| 9 | SaveImage | 保存输出 |

### LoRA 加载

**关键发现**：z-image LoRA 存放在 `loras/z-image/` 子目录。ComfyUI 的 LoraLoader 节点不自动扫描子目录，但支持**相对路径格式**。

```json
{
    "40": {"class_type": "LoraLoader", "inputs": {
        "model": ["28", 0],
        "clip": ["30", 0],
        "lora_name": "z-image/UwU_Clarity_Zimg_v3.safetensors",
        "strength_model": 0.7,
        "strength_clip": 0.7
    }}
}
```

**❌ Symlink 方案失败**：在顶层 `loras/` 目录创建 symlink 指向子目录文件，ComfyUI 无法正确解析。

### 多 LoRA 节点结构（链式）

```
UNETLoader(28) ──→ model ──→ LoraLoader(40) ──→ model_lora ──→ ModelSamplingAuraFlow(11) ──→ KSampler(3)
CLIPLoader(30) ──→ clip  ──→ LoraLoader(40) ──→ clip_lora  ──→ CLIPTextEncode(27)
```

每个 LoRA 用独立 LoraLoader 节点，chain 连接。

### Prompt 结构模板

```
(style keyword:1.3), (technique:1.4), (color palette:1.3),
masterpiece, best quality,
[人物描述], [动作/姿势], [场景/氛围],
[lighting], [atmosphere],
(visible anatomical details:1.4), (proper body proportions:1.3)
```

---

## 四、LoRA 目录

### solo_lee SoloLoRA 系列（12个）

| LoRA 文件 | 风格 | 推荐权重 |
|-----------|------|----------|
| `InkPortrait_SoloLoRA_ZITv1` | 水墨肖像 | 0.7 |
| `DSM_SoloLoRA_ZITv1` | 水墨天女 | 0.5 |
| `FieldHush_SoloLoRA_ZITv1_e` | 水彩+墨笔+动漫融合 | 0.7 |
| `Asuka_SoloLoRA_ZITv2` | 明日香角色 | 0.7 |
| `ArtBot_SoloLoRA_ZITv1` | 艺术机器人/机械风 | 0.7 |
| `InkBook_SoloLoRA_ZITv1` | 水墨绘本 | 0.7 |
| `3DOrigami_SoloLoRA_ZITv1` | 3D折纸几何 | 0.7 |
| `AerithG_SoloLoRA_ZIBv1` | 爱丽丝·盖恩斯伯勒 | 0.7 |
| `Mecha_SoloLoRA_ZITv1` | 机甲战士 | 0.7 |
| `GloomFable_SoloLoRA_ZITv1` | 暗黑童话 | 0.7 |
| `DigitalSurreal_SoloLoRA_ZITv2` | 数字超现实 | 0.7 |
| `ClassicBeauty_SoloLoRA_Zv3` | 古典美/文艺复兴 | 0.7 |

### 亚洲风格（3个）

| LoRA 文件 | 风格 | 推荐权重 |
|-----------|------|----------|
| `hina_zImageTurbo_asianMix_v2.56` | 亚洲混合风 | 0.7 |
| `shengtang_000004000` | 盛唐/中国宫廷风 | 0.7 |
| `ancient Chinese outfit v4` | 中国古代服饰 | 0.6-0.7 |

### NSFW 专用（16个）

| LoRA 文件 | 功能 | 推荐权重 | 实测评分 |
|-----------|------|----------|---------|
| `NSFW_master_ZIT_000017532` | NSFW 合并大模型（593MB） | 0.3-0.5 | ⭐8.5/10 🔥首选 |
| `B_NSFW_v2_z_image_lora` | NSFW v2 合并模型（649MB） | 0.3-0.5 | 未测 |
| `uncut_penis_ZIT_v1` | 男性器官强化 | 0.5-0.6 | ⚠️7/10 拖累画质 |
| `zimage_nudismslider_000000150` | 裸体程度滑块 | 0.5-0.7 | 未测 |
| `zimage_luisafemalnudismv2` | 女性裸体增强 | 0.3-0.5 | ⭐稳定 |
| `PornMaster_Speculum_zimage_v1_lora_B` | 情色器具 | 0.6 | 未测 |
| `SexMachv1` | 性爱姿态 | 0.6 | 未测 |
| `zimage-perform woman fucking penis` | 性行为姿态 | 0.7 | 未测 |
| `pussy-zimage-v1_000026000` | 女性器官细节 | 0.5-0.7 | 未测 |
| `BreastSize_Slider_m2_to_p2` | 胸部大小滑块 | 0.7 | 未测 |
| `round_breasts_zimg` | 胸部形状 | 0.6 | 未测 |
| `Perky Tits` | 胸部挺拔 | 0.6 | 未测 |
| `hyper gigantic tits` | 巨乳强化 | 0.7 | 未测 |
| `fake_real_loraholic` | 胸部真实感 | 0.6 | 未测 |
| `RLY-thighgapV1_1` | 大腿间隙 | 0.6 | 未测 |
| `m99_labiaplasty_pussy_3_zimageturbo` | 私处形态调整 | 0.7 | 未测 |

### 风格化（16个）

| LoRA 文件 | 风格 | 推荐权重 |
|-----------|------|----------|
| `FashionSketch_SoloLoRA_Zv1` | 时尚草稿/素描风格 | 0.7 |
| `UwU_Clarity_Zimg_v3` | 清晰度增强 | 0.5-0.6 |
| `better_images_loraholic` | 画质增强 | 0.5 |
| `Z-Brushwork` | 粗笔刷质感 | 0.7 |
| `Joseph_Zubukvic_Sketch_E8` | 素描风格 | 0.7 |
| `Illustration 6T2_E9` | 插画风格 | 0.5 |
| `Inspiration_V3T1_E0` | 灵感风格 | 0.5 |
| `Exogenous_E8` | Bradhamel 画风 | 0.7 |
| `retro_cyberpunk_fusion_z_image_turbo_000012000` | 赛博朋克 | 0.6 |
| `retro_neo_noir_style_z_image_turbo` | 黑色电影 | 0.6 |
| `dark_synth_anime_z_image_turbo_000006000` | 暗黑合成动漫 | 0.6 |
| `zimage_experimental_jojo` | JoJo风格 | 0.7 |
| `tattoo Z` | 纹身增强 | 0.7 |
| `zentai1` | 紧身衣/连体衣 | 0.7 |
| `zimage_underview_ep_v4` | 仰视角度 | 0.7 |
| `consistent_char_min_park_z_image` | 角色一致性 | 0.6 |

### 身体特征（2个）

| LoRA 文件 | 功能 | 推荐权重 |
|-----------|------|----------|
| `legs with stockings` | 丝袜腿部 | 0.7 |
| `zentai1` | 紧身衣包裹 | 0.7 |

---

## 五、已验证参数配置

### V5 — Risograph 印刷风

| 参数 | 值 |
|------|-----|
| Steps | 6 |
| CFG | 1 |
| 分辨率 | 1024×1560 |
| Sampler | res_multistep |
| Scheduler | simple |
| Shift | 3 |

**LoRA 组合（4链）：**

| LoRA | 功能 | 权重 |
|------|------|------|
| FashionSketch_SoloLoRA_Zv1 | 时尚草稿风格 | 0.3 |
| Z-Brushwork | 粗笔刷质感 | 0.25 |
| uncut_penis_ZIT_v1 | 男性器官强化 | 0.6 |
| UwU_Clarity_Zimg_v3 | 清晰度增强 | 0.4 |

验证记录：
- 2026-05-13 V5：2人全裸构图（1girl+1boy），成功
- 2026-05-13 V5 改造：3人国风女王加冕（1girl+2boys），成功

---

## 六、权重校准经验

| 场景 | 权重策略 | 效果 |
|------|----------|------|
| 风格 LoRA（FashionSketch/Z-Brushwork） | 0.25-0.3 | 肢体正确 + 风格保留 |
| 风格 LoRA 全 0.7 | 0.7 | 手指畸变，过度风格化 |
| NSFW 功能 LoRA（uncut_penis） | 0.6-0.7 | 正常，效果稳定 |
| 画质增强（UwU_Clarity） | 0.4-0.5 | 足够，无需更高 |
| 中国风 LoRA（shengtang/ancient Chinese） | 0.6-0.7 | 宫廷服饰风格明显 |

### 多 LoRA 总权重建议
- 主画风 0.6
- 辅助 0.3-0.5
- 功能 0.5-0.7
- 加载顺序：主画风 → 质感/辅助 → 清晰度 → NSFW 专用

### 大型合并模型
- NSFW_master (593MB)、B_NSFW_v2 (649MB)：权重 0.5-0.7，不宜过高

---

## 七、使用注意事项

1. **路径格式**：`z-image/文件名.safetensors`（子目录路径，不是顶层 symlink）
2. **多 LoRA 串联**：每个用独立 LoraLoader 节点，chain 连接
3. **权重校准**：降低到 0.4-0.6 让风格融合更自然
4. **NSFW 功能 LoRA**（如 uncut_penis）保持 0.7 效果较好
5. **画质增强 LoRA**（如 UwU_Clarity）0.5 即可
6. **ComfyUI 启动**后建议 sleep 20-30s 再提交 workflow
