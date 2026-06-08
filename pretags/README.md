# Pretags 数据文件使用说明

本项目提供示例 pretags 数据文件作为基础模板。

## 📋 初次使用

1. **复制示例文件**：
   ```bash
   cd pretags/
   cp example-pretags-anima.json pretags-anima.json
   cp example-pretags-ill-noob.json pretags-ill-noob.json
   ```

2. **根据需要选择工作流**：
   - `pretags-anima.json` - 用于 Anima/Flux 工作流
   - `pretags-ill-noob.json` - 用于 Illustrious/Noob 工作流

3. **开始使用**：
   ```bash
   export PRETAGS_DATA_PATH=./pretags/pretags-anima.json
   # 或让系统自动检测
   ```

## 🔒 Git 保护

- `example-pretags-*.json` - 示例模板，会被 git 跟踪
- `pretags-*.json` - 你的实际数据，**不会被 git 跟踪**

这样你可以随意修改 `pretags-anima.json`，不用担心 git pull 覆盖你的更改。

## 📝 更新数据

**添加角色/标签**：
直接编辑 `pretags-anima.json` 或使用工具：
```bash
# 使用 Web 界面编辑
cd modules/Tanger-Presets-Show
python3 server.py

# 或使用批量导入工具
cd tools/pretags-batch-import
python import_from_excel.py
```

**从示例同步新数据**：
如果项目更新了示例模板，你可以手动合并：
```bash
# 备份你的数据
cp pretags-anima.json pretags-anima.backup.json

# 查看示例文件的变化
git diff HEAD~1 example-pretags-anima.json

# 手动合并需要的部分
```

## 🔄 数据文件位置优先级

系统会按以下顺序查找 pretags 数据：

1. `$PRETAGS_DATA_PATH` 环境变量
2. `pretags/pretags-anima.json` 或 `pretags/pretags-ill-noob.json`
3. `modules/Tanger-Presets-Show/data/pretags.json`（符号链接）

## 📊 数据文件说明

### example-pretags-anima.json
- **大小**: ~19 MB
- **工作流**: Anima (Flux)
- **内容**: 19,000+ 角色，不含 SDXL LoRA

### example-pretags-ill-noob.json
- **大小**: ~20 MB
- **工作流**: Illustrious/Noob (SDXL)
- **内容**: 19,000+ 角色，含 SDXL LoRA

## ⚠️ 注意事项

- ⚠️ 不要直接修改 `example-pretags-*.json`（会被 git 跟踪）
- ⚠️ 修改前备份你的 `pretags-*.json` 文件
- ⚠️ 大型修改建议通过 Excel 导入导出工具

---

**相关文档**:
- [Pretags 数据管理](../references/pretags-data-management.md)
- [Pretags Excel 导入导出](../references/pretags-excel-workflow.md)
