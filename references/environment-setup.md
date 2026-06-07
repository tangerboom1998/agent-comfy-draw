# 环境配置

项目环境变量和目录结构配置。

## 核心概念

- **环境变量** - 通过 `.env` 文件配置路径
- **模型类型** - 根据文件名关键字自动检测（anima/noob/z-image）
- **分类目录** - 按类型和类别组织 LoRA 文件

## 环境变量

通过 `.env` 文件配置（从 `.env.example` 复制）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LORA_MODEL_DIR` | `/opt/comfyui/models/loras` | LoRA 模型根目录 |
| `COMFYUI_ROOT` | `/opt/comfyui/ComfyUI` | ComfyUI 安装目录 |
| `COMFYUI_HOST` | `http://127.0.0.1:8188` | ComfyUI 服务地址 |

## LoRA 目录结构

```
$LORA_MODEL_DIR/
├── anima/                  # Anima 模型
│   ├── 人物/               # 角色 LoRA
│   ├── 服装/               # 服装 LoRA
│   ├── 画风/               # 画风 LoRA
│   └── 其他/               # 其他
├── illustrious&noob/       # SDXL 模型
│   ├── 人物/
│   ├── 服装/
│   ├── 画风/
│   └── 其他/
└── z_image_turbo/          # z-image 模型
    ├── 人物/
    ├── 服装/
    ├── 画风/
    └── 其他/
```

## 模型类型自动检测

根据文件名关键字自动分类：

| 关键字 | 模型类型 |
|--------|---------|
| `anima` | anima/ |
| `noob`, `illustrious` | illustrious&noob/ |
| `turbo`, `z_image` | z_image_turbo/ |

**示例**:
- `character_anima.safetensors` → `anima/人物/`
- `style_noob.safetensors` → `illustrious&noob/画风/`

## 相关文档

- [Pretags 数据管理](./pretags-data-management.md)
- [ComfyUI 启动](../tools/comfyui-startup/SKILL.md)

---

**最后更新**: 2026-06-08
