# FaceDetailer 管线节点结构

当前默认工作流：`assets/noob_api_fix_upscale_face_detailer.json`

## 完整管线

```
                                    ┌─────────────────────────┐
                                    │  67: CheckpointLoader   │
                                    └──────────┬──────────────┘
                                               │
                                    ┌──────────▼──────────────┐
                                    │ 84: FEEncLoraAutoLoader │
                                    └──────────┬──────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
         ┌─────────▼──────────┐    ┌──────────▼─────────┐    ┌──────────▼─────────┐
         │ 10: CLIPTextEncode │    │ 48: KSampler Adv   │    │ 14: CLIPTextEncode │
         │ (positive prompt)  │    │ (Efficient)        │    │ (negative prompt)  │
         └─────────┬──────────┘    └──────────┬─────────┘    └──────────┬─────────┘
                   │                          │                         │
                   │              ┌───────────┼───────────┐             │
                   │              │           │           │             │
                   │    ┌─────────▼──┐  ┌─────▼─────┐  ┌──▼──────────┐  │
                   │    │ 91: Pre-  │  │ 101: Face │  │ 92: Model-  │  │
                   │    │ viewImage │  │ Detailer  │  │ Sampling-   │  │
                   │    │ (raw)     │  │           │  │ Discrete    │  │
                   │    │ → _0.png  │  └─────┬─────┘  └─────────────┘  │
                   │    └───────────┘        │                         │
                   │                         │                         │
                   │              ┌──────────▼──────────┐              │
                   │              │ 102: PreviewImage   │              │
                   │              │ (face-detailered)   │              │
                   │              │ → _2.png ✅         │              │
                   │              └─────────────────────┘              │
                   │                                                    │
                   │    (如果启用 --upscale)                             │
                   │                                                    │
                   │              ┌──────────▼──────────┐               │
                   │              │ 94: UltimateSD-     │               │
                   │              │     Upscale         │               │
                   │              └──────────┬──────────┘               │
                   │                         │                          │
                   │              ┌──────────▼──────────┐               │
                   │              │ 110: FaceDetailer   │               │
                   │              │ (二次面部修复)      │               │
                   │              └──────────┬──────────┘               │
                   │                         │                          │
                   │              ┌──────────▼──────────┐               │
                   │              │ 97: PreviewImage    │               │
                   │              │ → _4.png ✅         │               │
                   │              └─────────────────────┘               │
```

## 各节点作用

| 节点 ID | 类型 | 输入来源 | 输出 |
|---------|------|----------|------|
| 67 | CheckpointLoader | 加载基础模型 (noobaiXL) | model, clip, vae |
| 84 | FEEncLoraAutoLoader | 加载 LoRA（支持多 LoRA 串联） | model, clip |
| 10 | BNK_CLIPTextEncodeAdvanced | 正面提示词输入 (from 85 FETextInput) | positive conditioning |
| 14 | BNK_CLIPTextEncodeAdvanced | 负面提示词输入 | negative conditioning |
| 48 | KSampler Adv. (Efficient) | 核心采样器 — 模型 + 正向/反向 + latent | 原始图像 (output[5]) |
| 91 | PreviewImage | ← 48[5] (raw KSampler) | **`_0.png` — 原始输出（无面部修复）** |
| 101 | FaceDetailer | ← 48[5] (raw) + 48[0] (model) + 10 (pos) + 14 (neg) | 面部修复后的图像 |
| 102 | PreviewImage | ← 101[0] | **`_2.png` — 第一遍 FaceDetailer 修复** ✅ |
| 83 | FESaveEncryptImage | ← 101[0] | **`_1.epng` — 加密格式，忽略** |
| 92 | ModelSamplingDiscrete | ← 67[0] (model) | 调整模型采样参数 |
| **94** | UltimateSDUpscale | ← 102 (face-detailered) | **仅 `--upscale` 开启时激活** |
| **110** | FaceDetailer (二次) | ← 94 (upscaled) | **仅 `--upscale` 开启时激活** |
| **97** | PreviewImage | ← 110[0] | **`_4.png` — 放大 + 二次面部修复** ✅ |
| 96 | FESaveEncryptImage | ← 110[0] | **`.epng` — 加密格式，忽略** |
| 109 | UltralyticsDetectorProvider | 提供 bbox 检测器 | 给 FaceDetailer 101/110 用 |

## 图片输出规则

### 不开启 `--upscale`

| 文件 | 节点 | 内容 | 发送? |
|------|------|------|-------|
| CCUI_*_0.png | 91 | KSampler 原始输出 | ❌ |
| CCUI_*_1.epng | 83 | FESave 加密 | ❌ 忽略 |
| CCUI_*_2.png | 102 | FaceDetailer 101 修复后 | **✅ 发送这张** |

### 开启 `--upscale`

| 文件 | 节点 | 内容 | 发送? |
|------|------|------|-------|
| CCUI_*_0.png | 91 | KSampler 原始 | ❌ |
| CCUI_*_1.epng | 83 | FESave | ❌ |
| CCUI_*_2.png | 102 | FaceDetailer 101 | ❌（不是最好的） |
| CCUI_*_3.epng | 96 | FESave (upscaled) | ❌ |
| CCUI_*_4.png | 97 | FaceDetailer 110 (放大+二次修复) | **✅ 发送这张** |

## FaceDetailer 参数

两个 FaceDetailer 节点参数几乎相同，仅 seed 不同：

| 参数 | 节点 101 | 节点 110 |
|------|----------|----------|
| guide_size | 512 | 512 |
| max_size | 1024 | 1024 |
| steps | 50 | 50 |
| cfg | 7 | 7 |
| denoise | 0.3 | 0.3 |
| feather | 5 | 5 |
| force_inpaint | true | true |
| bbox_threshold | 0.5 | 0.5 |
| bbox_dilation | 10 | 10 |
| bbox_crop_factor | 3 | 3 |
| sam_detection_hint | center-1 | center-1 |
| sam_threshold | 0.93 | 0.93 |
| seed | 876867078587998 | 730645543639622 |
