# Pretags Excel 导入导出

Pretags 数据与 Excel 文件之间的转换流程。

## 核心概念

- **Excel 格式** - Pretags 数据的可编辑表格格式
- **导入导出** - 数据在 JSON 和 Excel 之间转换
- **批量编辑** - 通过 Excel 批量修改数据

## 使用场景

### 场景 1: 导出到 Excel

**步骤**:
1. 读取 pretags.json
2. 转换为 Excel 格式
3. 每个类别一个 sheet

**示例**:
```bash
python export_to_excel.py \
  --input pretags/pretags-anima.json \
  --output pretags_anima.xlsx
```

### 场景 2: 从 Excel 导入

**步骤**:
1. 读取 Excel 文件
2. 验证数据格式
3. 合并到 pretags.json
4. 处理冲突（ID 相同）

**示例**:
```bash
python import_from_excel.py \
  --input pretags_anima.xlsx \
  --output pretags/pretags-anima.json
```

### 场景 3: 批量修改

**工作流**:
1. 导出 Excel
2. 在 Excel 中编辑（添加、修改、删除）
3. 导入回 JSON
4. 验证数据完整性

## 注意事项

- ⚠️ 导入前备份原始 JSON 文件
- ⚠️ Excel 中的 ID 不可修改
- ⚠️ Docker 环境需要安装 openpyxl

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags 批量导入](../tools/pretags-batch-import/SKILL.md)
- [Pretags 数据管理](./pretags-data-management.md)

---

**最后更新**: 2026-06-07
