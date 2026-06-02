# Pretags 数据管理

> 合并自: pretags-parent-entry-detection.md, pretags-dual-path-sync.md, batch-migration-pretags.md, lora-download-and-registration.md, lora-path-resolution-pitfall.md

---

## 一、父条目检测与清理

### 背景

当同一角色有多个服装变体时，可能出现"父条目"——包含通用属性但没有特定服装的条目。例如：

- `katya`（父条目，无特定服装） ← 应删除
- `katya-def clothes`（子条目，默认服装） ← 保留
- `katya-s1 bikini`（子条目，泳装） ← 保留

### 核心指标

| 指标 | 说明 |
|------|------|
| 同一 `lora_file` | 父条目和子条目使用同一个 LoRA 文件 |
| tags 非空但无 clothing 细分 | 父条目的 tags 不包含特定服装标识 |
| 存在多个同名前缀条目 | `katya` / `katya-def` / `katya-s1` 等 |

### 检测关键词

```python
# 匹配 "katya-def clothes", "katya-s1 bikini", "mon3tr def clothes" 等
import re
VARIANTS_PATTERN = re.compile(r'-(def|s\d|alt|v\d)\s', re.IGNORECASE)
```

### 重复属性检测

如果父条目的 tags 和子条目的 tags 高度重叠（>80%），父条目是冗余的。

### 完整检测脚本

```python
import json, re
from collections import defaultdict

with open('pretags.json') as f:
    data = json.load(f)

# 按 lora_file 分组
by_lora = defaultdict(list)
for cid, info in data.get('characters', {}).items():
    lf = info.get('lora_file', '')
    if lf:
        by_lora[lf].append((cid, info))

# 检测父条目
suspects = []
for lora_file, entries in by_lora.items():
    if len(entries) < 2:
        continue
    names = [info.get('name', '') for _, info in entries]
    for cid, info in entries:
        name = info.get('name', '')
        # 如果存在以 name + '-' 开头的其他条目，name 可能是父条目
        children = [n for n in names if n.startswith(name + '-') and n != name]
        if children:
            suspects.append((cid, name, children, lora_file))

print(f"共发现 {len(suspects)} 个疑似父条目")
for cid, name, children, lora_file in suspects:
    print(f"  [{cid}] {name} → 子条目: {children}")
```

### 分组确认法（防止误报）

```python
# 对每个父条目，检查同一 lora_file 下是否有细分条目
confirmed = []
for cid, name, children, lora_file in suspects:
    # 检查父条目的 tags 是否与子条目高度重叠
    parent_tags = set(data['characters'][cid].get('tags', '').split(','))
    child_tags_all = set()
    for child_name in children:
        for ccid, cinfo in data['characters'].items():
            if cinfo.get('name') == child_name:
                child_tags_all.update(cinfo.get('tags', '').split(','))
    overlap = len(parent_tags & child_tags_all) / max(len(parent_tags), 1)
    if overlap > 0.8:
        confirmed.append((cid, name))
```

### ⚠️ 注意事项

1. **不要假设同名条目是重复**：必须比对 model file name
2. **父条目可能包含不同 lora_file 的条目**：先按 lora_file 分组
3. **server.py 覆盖 CLI 修改**：杀 server → 修改 → 启动 server

### 确认后删除流程

1. 备份 pretags.json
2. 在 Excel 中审核确认列表
3. 删除确认的父条目
4. 更新 charsort（如果存在）

```bash
# 备份
cp pretags.json pretags_backup_parent_$(date +%s).json

# 导出审核 Excel
python -c "
import json
from openpyxl import Workbook
with open('pretags.json') as f: d = json.load(f)
wb = Workbook()
ws = wb.active
ws.title = '父条目审核'
ws.append(['ID', '名称', 'Tags', '子条目', '确认删除'])
# ... 填充数据
wb.save('tmp/pretags_父条目审核.xlsx')
"
```

---

## 二、LoRA 模型管理

### LoRA 下载与注册

```bash
# Step 1: 查找角色
lark-cli civitai-api +search --query "character_name" --type LORA

# Step 2: 用 civitai-api 下载
lark-cli civitai-api +download --model-id 12345 --output-dir downloads/

# Step 3: 重命名为 pretags lora_file
mv downloads/original_name.safetensors loras/人物/new_name.safetensors

# Step 4: 放入对应 model_type 目录
# 人物 → loras/人物/
# 画风 → loras/画风/
# 服装 → loras/服装/

# Step 5: 确认 ComfyUI 识别
ls loras/*/new_name.safetensors
```

### LoRA 路径解析 Pitfall

**问题**：`FEEncLoraAutoLoader` 节点使用 stem-only 名称（如 `my_lora` 而非 `my_lora.safetensors`）时，如果存在同名不同路径的文件，缓存可能返回错误的文件。

**根因**：ComfyUI 的 `folder_paths.get_full_path_or_raise` 在多个子目录有同名文件时，行为不确定。

**规则**：始终使用完整相对路径格式（如 `z-image/my_lora.safetensors`）。

### 批量迁移 LoRA + Pretags

适用场景：从其他来源批量导入 LoRA 文件并创建 pretags 条目。

#### Step 1: 扫描源目录

```bash
# 源目录分类 → 目标目录映射
find /source/loras/ -name "*.safetensors" | while read f; do
    # 检测 model_type 并移动到对应目录
done
```

#### Step 2: Hash 冲突检测

```python
import hashlib, os
existing = {}
for f in os.listdir(target_dir):
    h = hashlib.sha256(open(os.path.join(target_dir, f), 'rb').read()).hexdigest()[:16]
    existing[h] = f

for f in os.listdir(source_dir):
    h = hashlib.sha256(open(os.path.join(source_dir, f), 'rb').read()).hexdigest()[:16]
    if h in existing:
        print(f"冲突: {f} ↔ {existing[h]}")
```

#### Step 3: 创建 Pretags 条目

##### 服装条目（Lora=1）

```python
entry = {
    'name': '服装名称',
    'lora_file': 'xxx.safetensors',
    'description': '服装描述',
    'model_type': '服装',
    'tags': '触发词1, 触发词2, ...',
    'tags_count': 2,
}
```

##### 人物条目（Lora=1）— 三类 tag 拆分

```python
entry = {
    'name': '角色名',
    'lora_file': 'xxx.safetensors',
    'tags': '角色名, 外貌描述, 服装描述',  # name + appearance + clothing
    'tags_count': 3,
    'series': '系列名',
    'categories': ['分类1', '分类2'],
}
```

#### Step 4: 匹配检查

验证所有文件都有 pretags 条目：

```python
# 检查各目录模型数
import os, json
with open('pretags.json') as f:
    data = json.load(f)

for model_type in ['人物', '画风', '服装', '动作', '镜头', '场景', '其他']:
    dir_files = set(os.listdir(f'loras/{model_type}/'))
    pretags_files = set(
        info['lora_file'] for info in data.get(model_type, {}).values()
        if info.get('lora_file')
    )
    missing = dir_files - pretags_files
    if missing:
        print(f"{model_type}: {len(missing)} 个文件缺少 pretags")
```

### activation text 是 pretags tag 的主要来源

从 Civitai API 的 `trainedWords` 字段提取，或从 safetensors 元数据 `ss_tag_frequency` 提取。

### 陷阱：切勿假设同名条目是重复

```python
# ❌ 错误：看到 name 相似就删除
if entries_have_similar_names:
    delete_duplicates()

# ✅ 正确：比对 lora_file
if entries_have_same_lora_file:
    check_if_parent_or_duplicate()
```

---

## 三、双路径同步问题

### 问题描述

pretags.json 同时存在于 `skills/` 和 `skill_hub/` 两个路径下，修改其中一个不会自动同步另一个。

### 症状
- Tanger-Presets-Show 显示的条目与 CLI 查询不一致
- 之前修改的条目"丢失"了

### 正确做法

```bash
# 确认两个文件是否一致
diff skills/pretags.json skill_hub/pretags.json

# 如果不一致，以 skills/ 为准
cp skills/pretags.json skill_hub/pretags.json
```
