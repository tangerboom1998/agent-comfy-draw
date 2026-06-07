# Pretags Draw 使用规则

Pretags Draw 模块的核心使用规则和最佳实践。

## 提示词构建规则

### 角色名识别

系统自动查询 pretags 数据库识别中文角色名。

**查询方法**：
```bash
python scripts/pretags_manager.py search <角色名>
```

### 必需字段

使用 pretags 构建提示词时必须包含：

- `name` - 角色英文名（不可省略，即使有 LoRA）
- `tags` - 基础标签
- `appearance` - 外观描述
- `clothing` - 服装描述

**示例**：
```python
prompt = f"masterpiece, best quality, {name}, {tags}, {appearance}, {clothing}"
```

### Solo 标签

**单角色绘图必须包含 `solo` 标签**，避免重影和多人物。

**正确示例**：
```
masterpiece, best quality, solo, (zhezhi:1.3), 1girl, long hair
```

## Tag Producer 预设

### 支持的指令

| 指令格式 | 示例 | 说明 |
|---------|------|------|
| 人物 | `折枝 服装 外貌 0.9` | 查 pretags 生成 tag + LoRA |
| 类别 | `动作 坐着` | 动作/服装/画风/场景 |
| 画师 | `撸串 4` | 随机选取 4 个画师 |

### 使用示例

```bash
python tag_producer.py "折枝 服装 外貌 动作 坐着 画风 2d润彩 撸串 3"
```

## 提示词层级

Agent 构建提示词的标准顺序：

```
画质 → 画风 → 主体 → 服装 → 表情 → 身材 → 姿势 → 
镜头 → 场景 → 光影 → 画师
```

## 质量检查

Agent 执行的 12 项检查：

1. 零中文字符
2. 画质前缀完整
3. 主体明确
4. 服装描述
5. 表情描述
6. 身材描述
7. 姿势描述
8. 镜头角度
9. 场景设定
10. 光影效果
11. 权重合理
12. 画师标签

## 相关文档

- [Pretags Draw SKILL](../modules/pretags-draw/SKILL.md)
- [角色预览图生成](./character-preview-generation.md)

---

**最后更新**: 2026-06-07
