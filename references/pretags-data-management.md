# Pretags 数据管理

Pretags 数据库的管理、清理和维护指南。

## 核心概念

- **父条目** - 同一角色的通用条目，包含多个服装变体
- **子条目** - 特定服装或形态的条目
- **ID-key 系统** - 基于 MD5 的 8 字符稳定 ID

## 使用场景

### 场景 1: 检测父条目

**识别标准**:
- 同一 `lora_file` 有多个条目
- 存在带后缀的变体（`-def`, `-s1`, `-alt`）
- 父条目 tags 与子条目高度重叠（>80%）

**步骤**:
1. 按 `lora_file` 分组所有条目
2. 检测带变体后缀的条目组
3. 对比 tags 重叠度
4. 手动确认后删除父条目

### 场景 2: LoRA 路径解析

**路径优先级**:
1. 完整路径匹配
2. Stem 名称匹配（不带扩展名）
3. 相对路径匹配

**示例**:
```python
# 优先级 1: 完整路径
lora_file = "画风/jijia-gnoob-000014.safetensors"

# 优先级 2: Stem 名称
lora_file = "jijia-gnoob-000014"

# 优先级 3: 相对路径
lora_file = "画风/jijia-gnoob-000014"
```

### 场景 3: 批量迁移

**从旧格式迁移到 ID-key 格式**:

**步骤**:
1. 为每个条目生成 MD5 ID
2. 将 name-key 映射转为 id-key 映射
3. 更新所有引用
4. 验证数据完整性

### 场景 4: 数据文件位置

**智能路径解析顺序**:
1. 环境变量 `PRETAGS_DATA_PATH`
2. 项目根目录 `pretags/` 目录
3. `modules/Tanger-Presets-Show/data/` 符号链接

## 注意事项

- ⚠️ 父条目检测需要手动确认，避免误删
- ⚠️ LoRA 文件路径统一使用 stem 名称（不带扩展名）
- ⚠️ 批量操作前务必备份数据

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags 批量导入](../tools/pretags-batch-import/SKILL.md)
- [Pretags Excel 工作流](./pretags-excel-workflow.md)
- [Pretags Draw 规则](./pretags-draw-rules.md)

---

**最后更新**: 2026-06-07
