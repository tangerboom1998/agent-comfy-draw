---
name: pretags-batch-import
description: "Pretags 数据批量导入工具：从 Civitai 获取模型元数据 → 标签分类 → 写入 pretags.json。支持分批处理、标签拆分、数据验证。"
version: 1.0.0
metadata:
  nanobot:
    emoji: "📦"
    requires:
      env: ["CIVITAI_API_KEY", "LORA_MODEL_DIR"]
---

# Pretags Batch Import

Pretags 数据批量导入工具，从 Civitai 下载模型元数据并规范化后写入 pretags 数据库。

## 🚀 快速开始

```bash
# 设置环境变量
export CIVITAI_API_KEY=your_api_key
export LORA_MODEL_DIR=/path/to/loras

# 从 Excel 合并导入角色/标签到 pretags（真实 CLI）
cd modules/pretags-draw/scripts
python pretags_merge_excel.py path/to/characters.xlsx --pretags ./pretags/pretags-anima.json

# 先试运行查看变更，不写盘
python pretags_merge_excel.py characters.xlsx --dry-run

# 修复 LoRA 字段格式（扫描磁盘文件对齐 model file name）
cd tools/pretags-batch-import/scripts
python fix_pretags_lora.py            # 直接修复并自动备份
python fix_pretags_lora.py --check    # 仅检查不写盘
```

## 🎯 核心功能

- **分批处理** - 每批 5-15 个模型，完整闭环后进入下一批
- **标签分类** - 自动拆分外貌和服装标签
- **数据验证** - 写入前验证 JSON 格式和字段完整性
- **LoRA 修复** - 修复和规范化 LoRA 字段格式

## ⚙️ 环境配置

**必需环境变量**:
- `CIVITAI_API_KEY` - Civitai API 密钥
  - 获取: https://civitai.com/user/account
- `LORA_MODEL_DIR` - LoRA 模型根目录
  - 示例: `/path/to/ComfyUI/models/loras`

**可选环境变量**:
- `PRETAGS_DATA_PATH` - Pretags 数据文件路径
  - 默认: `./pretags/pretags-anima.json`

**依赖**:
- Python 3.8+
- civitai-api 模块
- openpyxl (Excel 支持)

## 📖 使用示例

### 场景 1: 从 Excel 导入角色

```bash
cd modules/pretags-draw/scripts
# 准备 Excel 文件（包含角色名、来源、LoRA 信息），合并到 pretags
python pretags_merge_excel.py characters.xlsx --pretags ./pretags/pretags-anima.json

# 先试运行
python pretags_merge_excel.py characters.xlsx --dry-run
```

### 场景 2: 从 Civitai 发现并下载模型

批量发现 → 下载 → 标签拆分 → 写入 pretags 的完整管线见 [Civitai API](../../modules/civitai-api/SKILL.md#batch-model-import-pipeline)。

```bash
cd modules/civitai-api/scripts
# 扫描作者最新模型
python civitai.py models --username <creator> --sort "Newest" --nsfw true --limit 15
# 下载到对应分类目录
python civitai.py download-model <id> -o "$LORA_MODEL_DIR/人物/<name>.safetensors"
```

### 场景 3: 修复 LoRA 格式

```bash
cd tools/pretags-batch-import/scripts
# 仅检查，列出磁盘缺失/不一致的条目
python fix_pretags_lora.py --check
# 检查并修复（自动备份原文件）
python fix_pretags_lora.py
```

## 🔧 处理流程

### 5 步批量导入流程

```
1. 发现与清单
   - 获取模型元数据（hash、trainedWords）
   - 生成批次清单

2. 下载模型
   - 对比本地 hash
   - 下载缺失模型

3. 标签拆分 ⭐
   - 外貌 vs 服装分类
   - 去除污染标签
   - 规范化格式

4. 写入 pretags
   - 构建完整条目
   - JSON 验证
   - 批量写入

5. 验证
   - 测试 tag_producer
   - Hash 验证
   - 生成报告
```

### 标签分类规则

**外貌标签**:
- 种族/物种、发色/发型、瞳色
- 角/耳/尾/翅膀
- 体型特征、面部特征
- 纹身/身体标记、光环

**服装标签**:
- 衣物（dress/suit/kimono）
- 鞋袜、手套
- 头饰、首饰
- 眼镜/眼罩

详细规则：[Pretags Excel 导入导出](../../references/pretags-excel-workflow.md)

### 数据清洗

自动移除以下污染标签：
- 场景标签（white background）
- 画风标签（science fiction）
- 负向提示（no weapon）
- 重复标签

## 📚 相关文档

- [Pretags 数据管理](../../references/pretags-data-management.md) - 数据结构和管理规范
- [Pretags Excel 导入导出](../../references/pretags-excel-workflow.md) - Excel 格式和流程
- [Civitai API](../../modules/civitai-api/SKILL.md) - 模型元数据获取

## 📄 许可证

MIT License
