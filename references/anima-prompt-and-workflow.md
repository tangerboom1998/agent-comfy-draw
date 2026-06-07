# Anima Prompt 与工作流指南

Anima 模型（Flux 架构）的提示词编写规范和工作流配置。

## 核心概念

- **Flux 模型** - Anima 使用 Flux 架构，不兼容 SDXL LoRA
- **标签顺序** - 严格按照质量→风格→主体→场景的顺序
- **全小写** - 所有标签使用小写，逗号空格分隔

## Prompt 编写规范

### 标签顺序

```
质量标签 → 画师标签 → 角色描述 → 动作/姿势 → 场景/背景 → 光影
```

### 推荐前缀

**正面提示词**:
```
masterpiece, best quality, newest, latest, safe,
```

**负面提示词**:
```
lowres, worst quality, bad anatomy, bad hands, 
blurry, signature, watermark,
```

### 示例

```
masterpiece, best quality, newest, latest, safe, 
1girl, solo, silver hair, long hair, red eyes, 
white dress, standing, looking at viewer, 
castle background, moonlight, night sky,
```

## 使用场景

### 场景 1: 角色生图

**步骤**:
1. 添加质量前缀
2. 指定角色特征（发色、瞳色、服装）
3. 添加动作和场景
4. 设置参数（steps=28, cfg=5.5）

### 场景 2: 画风切换

**常用画师标签**:
- `@wlop` - 唯美幻想风
- `@ask` - 精美日系
- `@fu_mi` - 性感厚涂

### 场景 3: 工作流配置

**工作流文件**: `anima-new-Latent.json`

**环境要求**:
- `COMFYUI_WORKFLOW_PATH=./anima-new-Latent.json`
- 必须从 skill 根目录运行
- 需要 `aiohttp` 包

**参数配置**:
```bash
python comfyui_draw.py "prompt" \
  --canvas 竖图 --steps 28 --cfg 5.5
```

## 注意事项

- ⚠️ Anima 不支持 SDXL LoRA
- ⚠️ 工作流必须从 skill 根目录运行
- ⚠️ 需要 aiohttp 包（`pip install aiohttp`）

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags Draw](../modules/pretags-draw/SKILL.md)
- [工作流节点映射](./workflow-node-mapping.md)
- [z-image 工作流](./z-image-guide.md)

---

**最后更新**: 2026-06-07
