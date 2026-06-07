# 角色预览图生成

为 pretags 中的角色批量生成预览图（立绘）。

## 核心概念

- **预览图** - 角色的标准立绘图片，用于 Web 界面展示
- **批量生成** - 为所有带 LoRA 的角色生成预览图
- **标准规格** - 1024×1560 竖版立绘

## 使用场景

### 场景 1: 批量生成

**步骤**:
1. 筛选带 LoRA 的角色
2. 构建标准 prompt
3. 批量提交生成
4. 保存为预览图

**示例**:
```bash
# 全量生成（后台运行）
nohup python gen_character_previews.py --all > preview.log 2>&1 &

# 自定义参数
python gen_character_previews.py --all --steps 20 --cfg 5
```

### 场景 2: 单个角色生成

**手动生成流程**:
```bash
# 生成预览图
python comfyui_draw.py "masterpiece, best quality, solo, {character_tags}, standing, full body, simple white background" \
  --canvas 竖图 --steps 20

# 保存为预览图
cp output/CCUI_*.png previews/{character_id}.jpg
```

### 场景 3: 预览图规格

**推荐参数**:
- 分辨率: 1024×1560（竖版）
- Steps: 20-25
- CFG: 5-6
- 背景: simple white background
- 姿势: standing, full body

## 注意事项

- ⚠️ 必须添加 `solo` 标签防止重影
- ⚠️ 全量生成约需 3-4 小时
- ⚠️ 使用 FaceDetailer 输出作为最终预览图

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags Draw](../modules/pretags-draw/SKILL.md)
- [Pretags Draw 规则](./pretags-draw-rules.md)

---

**最后更新**: 2026-06-08
