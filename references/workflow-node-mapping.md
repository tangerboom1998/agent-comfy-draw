# 工作流节点映射表

ComfyUI Draw Suite 支持三种工作流类型，每种工作流使用不同的节点 ID 映射。

---

## 🎯 工作流类型识别

`comfyui_client.py` 通过文件名自动识别工作流类型：

| 工作流类型 | 文件名模式 | 模型架构 |
|-----------|-----------|---------|
| **Noob** (默认) | `noob_*` | SDXL (CheckpointLoader + CR Switch) |
| **Anima** | `anima_*` | Flux (UNETLoader + Qwen CLIP/VAE) |
| **z-image** | `z_image_*` 或 `zturbo` | Flux (UNETLoader + Qwen 4B CLIP) |

---

## 📊 节点 ID 映射表

### 基础参数节点

| 参数 | Noob | Anima | z-image |
|------|------|-------|---------|
| Prompt (正面提示词) | 85 | 10 | 31 |
| Negative (负面提示词) | 14 | 37 | 7 |
| Width (宽度) | 20 | 2 | 13* |
| Height (高度) | 21 | 3 | 13* |
| KSampler (采样器) | 48 | 30 | 3 |
| Seed (随机种子) | 32 | 4 | 51 |

\* z-image 的宽高在 EmptySD3LatentImage 节点中硬编码

### 放大节点

| 节点 | Noob | Anima | z-image |
|------|------|-------|---------|
| Upscale 起始节点 | 94 | 55 | 45 |
| Upscale 结束节点 | 97 | 62 | 50 |
| 节点范围 | 94-97 | 55-62 | 45-50 |

---

## 🏗️ Hires.fix 放大架构

### Noob 工作流

```
KSampler[48]
  ↓
UltimateSDUpscale[94] + UpscaleModelLoader[95]
  ↓
FaceDetailer[110] (bbox_detector 必需)
  ↓
Save[96] / Preview[97]
```

### Anima 工作流

```
KSamplerAdv[30]
  ↓
LatentUpscaleBy[55]
  ↓
KSampler[60] (二次采样)
  ↓
VAEDecode[56]
  ↓
FaceDetailer[59] (bbox_detector 必需)
  ↓
Preview[58] / Save[62]
```

### z-image 工作流

```
KSampler[3]
  ↓
LatentUpscaleBy[47]
  ↓
KSampler[45] (二次采样)
  ↓
VAEDecode[46]
  ↓
FaceDetailer[48] (bbox_detector 必需)
  ↓
Preview[49] / Save[50]
```

---

## ⚙️ 使用说明

### 自动节点映射

`comfyui_client.py` 会根据工作流文件名自动选择正确的节点映射：

```python
def _detect_workflow_type(workflow_path):
    filename = os.path.basename(workflow_path).lower()
    
    if 'anima' in filename:
        return 'anima'
    elif 'z_image' in filename or 'zturbo' in filename:
        return 'z-image'
    else:
        return 'noob'  # 默认
```

### 参数注入

生图时，参数会自动注入到正确的节点：

```python
# 例如设置提示词
if workflow_type == 'noob':
    workflow['85']['inputs']['text'] = prompt  # Noob 的 prompt 节点是 85
elif workflow_type == 'anima':
    workflow['10']['inputs']['text'] = prompt  # Anima 的 prompt 节点是 10
elif workflow_type == 'z-image':
    workflow['31']['inputs']['text'] = prompt  # z-image 的 prompt 节点是 31
```

### 放大功能

放大功能默认关闭 (`upscale=False`)。启用时：

```bash
python comfyui_draw.py "prompt" --upscale
```

不启用放大时，会自动移除放大路径的所有节点，避免资源浪费。

---

## 🔍 调试节点映射

如果生图参数未生效，检查节点 ID 是否正确：

```bash
# 1. 导出工作流 JSON
# 在 ComfyUI UI 中：Settings → Save (API Format)

# 2. 查找目标节点
cat workflow.json | jq '.[] | select(.class_type=="CLIPTextEncode")'

# 3. 确认节点 ID
# 输出中的 key 就是节点 ID
```

---

## 📚 相关文档

- [工作流架构详解](workflow-architecture.md)
- [ComfyUI API 参考](../modules/comfyui-api/references/rest-api.md)
- [故障排除](comfyui-pitfalls.md)

---

**最后更新**: 2026-06-07
