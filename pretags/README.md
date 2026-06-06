# Pretags 数据文件

此目录存储项目的核心角色标签数据文件。

## 数据文件说明

- **pretags-anima.json** (19MB) - Anima 工作流数据
  - 19,000+ 角色定义
  - 10,000+ 标签分类
  - 支持 Flux 模型架构

- **pretags-ill-noob.json** (20MB) - Illustrious/Noob 工作流数据
  - 角色和标签数据
  - 支持 SDXL 模型架构

## 数据结构

每个文件都使用 ID-key 结构（自 2026-05-20）：

```json
{
  "characters": {
    "c23fe569": {
      "id": "c23fe569",
      "cname": "角色中文名",
      "name": "character_english_name",
      "source": "来源作品",
      "appearance": "外观描述...",
      "clothing": "服装描述...",
      "has_lora": true,
      "lora_file": "模型文件名",
      "tags": ["tag1", "tag2", ...],
      "tags_count": 15
    }
  },
  "categories": {
    "画风": { ... },
    "动作": { ... },
    ...
  },
  "series": { ... },
  "metadata": {
    "total_characters": 19101,
    "total_categories": 10278,
    "last_updated": "2026-06-01"
  }
}
```

## 文件管理

这些文件通过 **Git LFS** 管理（见 `.gitattributes`）。

如果你克隆了仓库但没有数据文件：

```bash
# 确保已安装 Git LFS
git lfs install

# 拉取 LFS 文件
git lfs pull
```

## 如何使用

数据文件会被 Tanger-Presets-Show 自动加载：

```bash
# 方式 1：自动检测（默认）
cd modules/Tanger-Presets-Show
python server.py
# 自动搜索 ../../pretags/ 目录

# 方式 2：环境变量指定
export PRETAGS_DATA_PATH=/path/to/pretags-anima.json
python server.py

# 方式 3：在 .env 中配置
echo "PRETAGS_DATA_PATH=./pretags/pretags-anima.json" >> .env
```

## 数据更新

数据文件由项目维护者定期更新。如需手动更新：

1. 通过 Web 界面编辑（推荐）
2. 直接编辑 JSON 文件（需重启服务）
3. 使用批量导入工具

## 备份

数据文件会自动创建备份（`.bak` 扩展名），但不会提交到 Git。

如需恢复备份：

```bash
cp pretags-anima.json.bak pretags-anima.json
```

## 相关文档

- [Pretags 数据管理](../references/pretags-data-management.md)
- [Pretags Excel 导入导出](../references/pretags-excel-workflow.md)
- [数据文件管理指南](../DATA_MANAGEMENT.md)
