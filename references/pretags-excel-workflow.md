# Pretags Excel 导入导出工作流

> 合并自: pretags-excel-export.md, pretags-excel-export-workflow.md, pretags-excel-import-tag-merge.md

---

## 一、数据格式版本检测

### 当前格式（2026-05-16 后）

- 使用 ID-key 结构（MD5 8字符）
- `characters` 字段包含：`id, name, lora_file, tags, tags_count, preview, series, categories`
- `categories` 包含：`id, name, description, model_type`
- `series` 包含：`id, name, categories`

### 旧备份格式（2026-05-15 及更早）

- 使用 name-key 结构
- `characters` 字段不同，缺少 `id` 和 `tags_count`
- 需要特殊处理模板

---

## 二、导出到 Excel

### 快速导出（当前 schema，推荐）

```python
import json
from openpyxl import Workbook

with open('pretags.json') as f:
    data = json.load(f)

wb = Workbook()

# Characters sheet — 必须包含 tags
ws = wb.active
ws.title = "Characters"
headers = ['ID', '名称', 'LoRA文件', 'Tags', 'Tags数量', '预览图', '系列', '分类']
ws.append(headers)
for cid, info in data.get('characters', {}).items():
    ws.append([
        cid, info.get('name', ''), info.get('lora_file', ''),
        info.get('tags', ''), info.get('tags_count', 0),
        info.get('preview', ''), info.get('series', ''),
        ', '.join(info.get('categories', []))
    ])

# Categories sheets
for cat_name in ['画风', '人物', '服装', '动作', '镜头', '场景', '其他']:
    ws = wb.create_sheet(cat_name)
    ws.append(['ID', '名称', '描述', 'LoRA文件', '模型类型'])
    for cid, info in data.get(cat_name, {}).items():
        ws.append([
            cid, info.get('name', ''), info.get('description', ''),
            info.get('lora_file', ''), info.get('model_type', cat_name)
        ])

# Series sheet
ws = wb.create_sheet('Series')
ws.append(['ID', '名称', '分类'])
for sid, info in data.get('series', {}).items():
    ws.append([sid, info.get('name', ''), ', '.join(info.get('categories', []))])

wb.save('pretags_export.xlsx')
```

### 旧 schema 导出模板

```python
# Characters sheet — 旧格式兼容
headers = ['名称', 'LoRA文件', 'Tags', '预览图', '系列', '分类']

# 用此模板处理 2026-05-16 及更早的备份文件
```

### ⚠️ 关键规则：导出 Characters 必须包含 tags

导出 Excel 时，Characters sheet 必须包含 `tags` 列，否则导入时 tags 数据将丢失。

---

## 三、从 Excel 导入/合并

### Excel 格式要求

| 列 | 必填 | 说明 |
|----|------|------|
| ID | 否 | 8字符MD5，新建时自动生成 |
| 名称 | 是 | 条目名称 |
| LoRA文件 | 否 | safetensors 文件名 |
| Tags | 否 | 逗号分隔的标签 |
| Tags数量 | 否 | 自动计算 |
| 预览图 | 否 | 图片路径 |
| 系列 | 否 | 系列名称 |
| 分类 | 否 | 逗号分隔的分类名 |

### Tags 合并规则

导入时 tags 的处理：

1. **如果 Excel 中 tags 非空**：使用 Excel 的 tags（覆盖）
2. **如果 Excel 中 tags 为空**：保留 pretags.json 中已有的 tags
3. **name 字段**：`name + appearance + clothing` 合并为 tags

```python
# Tags 合并逻辑
name_tags = info.get('name', '').split(',')
appearance_tags = info.get('appearance', '').split(',')
clothing_tags = info.get('clothing', '').split(',')
merged = [t.strip() for t in name_tags + appearance_tags + clothing_tags if t.strip()]
info['tags'] = ', '.join(merged)
```

### 导入脚本

```python
import json
from openpyxl import load_workbook

# 读取 Excel
wb = load_workbook('pretags_import.xlsx')
ws = wb['Characters']

with open('pretags.json') as f:
    data = json.load(f)

# 导入
for row in ws.iter_rows(min_row=2, values_only=True):
    cid, name, lora_file, tags, tags_count, preview, series, categories = row
    # 新建或更新条目
    # ...

with open('pretags.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

---

## 四、批量操作

### 批量删除角色

```bash
# 1. 备份
cp pretags.json pretags_backup_$(date +%s).json

# 2. 删除（Python 脚本）
python -c "
import json
with open('pretags.json') as f: d = json.load(f)
d['人物'] = {k:v for k,v in d['人物'].items() if not ...}
with open('pretags.json','w') as f: json.dump(d, f, ensure_ascii=False, indent=2)
"

# 3. 保存
```

### 清空所有角色的 tags/tags_count

```python
for cid, info in data['characters'].items():
    info['tags'] = ''
    info['tags_count'] = 0
```

### 删除所有有 LoRA 的角色

```python
data['characters'] = {
    cid: info for cid, info in data['characters'].items()
    if not info.get('lora_file')
}
```

---

## 五、常见陷阱

### ⚠️ 命令中断陷阱

当批量操作被中断（Ctrl+C）时，pretags.json 可能处于不完整状态。**始终先备份**。

### ⚠️ Sandbox 环境 openpyxl 可用性

在 Docker sandbox 中，openpyxl 可能未安装：

```bash
pip install openpyxl
```

### ⚠️ 双目录陷阱

pretags.json 同时存在于 `skills/` 和 `skill_hub/` 目录时，确保修改的是正确的文件：

```bash
# 确认两个文件是否一致
diff skills/pretags.json skill_hub/pretags.json

# 如果不一致，以 skills/ 为准
cp skills/pretags.json skill_hub/pretags.json

# 如果错误修改了旧副本，同步到本体
cp skill_hub/pretags.json skills/pretags.json

# 重启 server
```

### ⚠️ server.py 覆盖 CLI 数据修改

Tanger-Presets-Show 的 `server.py` 会在内存中缓存 pretags.json 并在退出时覆盖写入。如果 server 在运行中，CLI 修改会被覆盖：

```bash
# ✅ 正确：杀 server → 修改 → 启动 server
kill $(pgrep -f server.py)
# 修改 pretags.json
python modules/Tanger-Presets-Show/server.py &

# ❌ 错误：server 运行中直接修改 pretags.json
```

---

## 六、发送文件

导出后通过 Discord 或其他渠道发送 Excel 文件。文件路径示例：

```
output/pretags_export_2026-05-17.xlsx
```
