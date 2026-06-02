# Pretags 补充入库工作流（已有模型）

当模型文件已存在于 `loras/` 目录但 pretags.json 中缺少对应条目时使用此流程。

## 与批量导入的区别

| | 批量导入（pretags-batch-import） | 补充入库（本文档） |
|--|------|------|
| 场景 | 从 Civitai 下载新模型 | 模型已存在，补 pretags |
| 来源 | Civitai API 搜索 | 本地目录扫描 |
| 下载 | 需要 | 不需要 |

## 流程

### Phase 1：扫描差异

```python
import json, os
from _env import LORA_MODEL_DIR

LORA_DIR = LORA_MODEL_DIR

with open('assets/pretags.json') as f:
    data = json.load(f)

# ⚠️ 必须收集「所有条目」的 model file name（不限 Lora 值），再用磁盘对比。
# 只收集 Lora==1 会把 Lora==0 但磁盘有文件的条目误判为「缺失」。
def collect_mfn(category_data):
    existing = set()
    for k, v in category_data.items():
        mfn = v.get('model file name', '')
        if isinstance(mfn, str) and mfn:
            existing.add(mfn.replace('.safetensors', ''))
    return existing

existing = collect_mfn(data['人物'])  # 包含 Lora=0 和 Lora=1

# 扫描所有 model_type/人物/ 子目录找差异
disk_files = set()
from _env import iter_lora_subdirs
for lora_dir in iter_lora_subdirs('人物'):
    for fn in sorted(os.listdir(lora_dir)):
        if fn.endswith('.safetensors'):
            disk_files.add(fn.replace('.safetensors', ''))

missing_in_pretags = disk_files - existing   # 磁盘有，pretags 完全无记录
missing_on_disk    = existing - disk_files   # pretags 有记录，磁盘无文件

print(f'磁盘有但 pretags 无: {len(missing_in_pretags)}')
for f in sorted(missing_in_pretags):
    print(f'  需入库: {f}')
print(f'pretags 有但磁盘无: {len(missing_on_disk)}')
```

### Phase 2：Civitai 查元数据

对每个缺失的模型：
1. 计算 SHA256 前 16 位
2. 用 `civitai-api` 的 `by-hash` 命令查 `trainedWords`
3. 获取角色名、触发词、外貌/服装 tag

```bash
cd skills/civitai-api
python scripts/civitai.py by-hash <hash_prefix>
```

⚠️ 代理必须可用（通过 `$HTTPS_PROXY` 或 `$ALL_PROXY` 环境变量配置）

### Phase 3：Tag 三类拆分

将 trainedWords 拆分为：
- `name`：角色触发词（如 `narmaya_(granblue_fantasy)`）
- `外貌`：身体特征（发色、瞳色、体型、种族特征等）
- `服装`：穿着饰品（衣服、饰品、武器等）

详见 `comfyui-draw/SKILL.md` 的「⚠️ 人物条目 Tag 三类拆分规则」

### Phase 4：写入 pretags.json

```python
data['人物']['角色名'] = {
    'cname': '角色名',
    'Source': '来源游戏',
    'Lora': 1,
    'model file name': '文件名（不含.safetensors）',
    'model hash': 'SHA256前10位',
    'unet weight': 0.8,
    'clip weight': 0.8,
    'link': 'https://civitai.com/models/XXXXX',
    'name': '触发词',
    '外貌': '1girl, ...',
    '服装': 'dress, ...',  # 无服装时为 0
}
```

### Phase 5：验证

```python
# 检查所有 Lora=1 条目的字段完整性
for cname, v in data['人物'].items():
    if v.get('Lora') == 1:
        assert v.get('name'), f'{cname}: name 缺失'
        assert v.get('外貌'), f'{cname}: 外貌缺失'
        # 服装允许为 0（无默认服装的角色）
```

## 特殊情况处理

### 多角色模型
一个 LoRA 包含多个角色 → 每个角色独立条目，共用 `model file name`

### 泳装/变体服装
必须独立建条目，不与默认服装合并

### Civitai 查不到的模型
- 用 JSON 文件的 `activation text` 字段作 fallback
- 仅作占位，等后续补充
