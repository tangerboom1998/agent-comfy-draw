# Agent 两级查询方案

当用户查询角色或标签信息时，Agent 使用两级查询系统：**优先 Pretags → 其次 Danbooru**

---

## 🎯 查询优先级

```
用户查询 "折枝的信息"
    ↓
[Level 1] 查询 Pretags 数据库
    ↓
   找到？
    ├─ YES → 返回 Pretags 完整信息（包含 LoRA、权重、本地化数据）
    └─ NO  → [Level 2] 查询 Danbooru API
              ↓
             找到？
              ├─ YES → 返回 Danbooru 标签信息（基础标签数据）
              └─ NO  → 告知用户未找到，建议添加到 Pretags
```

---

## 📊 两级查询对比

| 特性 | Level 1: Pretags | Level 2: Danbooru |
|------|-----------------|-------------------|
| **数据来源** | 本地 pretags.json | Danbooru API |
| **响应速度** | 极快（本地查询） | 慢（网络请求） |
| **信息完整度** | ✅ 完整（LoRA、权重、中文） | ⚪ 基础（英文 tag） |
| **LoRA 信息** | ✅ 有 | ❌ 无 |
| **中文名称** | ✅ 有 | ❌ 无 |
| **本地化数据** | ✅ 有（外观、服装） | ❌ 无 |
| **需要代理** | ❌ 不需要 | ✅ 需要 |

---

## 🔧 实现方案

### 查询流程代码示例

```python
def query_character(name: str) -> dict:
    """两级查询：Pretags → Danbooru"""
    
    # Level 1: 查询 Pretags
    result = query_pretags(name)
    if result:
        return {
            'source': 'pretags',
            'data': result,
            'has_lora': result.get('has_lora', False),
            'complete': True
        }
    
    # Level 2: 查询 Danbooru
    result = query_danbooru(name)
    if result:
        return {
            'source': 'danbooru',
            'data': result,
            'has_lora': False,
            'complete': False,
            'suggestion': '建议添加到 Pretags 以获取 LoRA 和本地化信息'
        }
    
    # 未找到
    return {
        'source': None,
        'data': None,
        'suggestion': '未找到该角色，可以手动添加到 Pretags'
    }

def query_pretags(name: str) -> dict:
    """查询 Pretags 数据库"""
    import subprocess
    result = subprocess.run(
        ['python', 'modules/pretags-draw/scripts/pretags_manager.py', 'search', name],
        capture_output=True, text=True
    )
    # 解析结果...
    return parsed_result

def query_danbooru(name: str) -> dict:
    """查询 Danbooru API"""
    import subprocess
    result = subprocess.run(
        ['python', 'modules/danbooru-tag-scraper/scripts/danbooru.py', 'character', name],
        capture_output=True, text=True
    )
    # 解析结果...
    return parsed_result
```

---

## 📋 不同场景的响应格式

### 场景 1: Pretags 找到（完整信息）

**查询**: "折枝的信息"

**Agent 响应**:
```
✅ 找到角色：折枝（zhezhi）

📍 数据来源：Pretags（本地数据库）

基本信息：
- 中文名：折枝
- 英文名：zhezhi
- 来源：鸣潮
- LoRA：✅ 有（zhezhi-anima，权重 0.9/0.9）

外观特征：
long hair, blue eyes, blue dress, white sleeves

服装：
blue dress, white sleeves, hair ornament

常用标签：
1girl, long_hair, blue_dress

使用方法：
在 tag_producer 中输入：折枝 服装 外貌 0.9
或直接使用：zhezhi, 1girl, solo, long hair, blue eyes
```

### 场景 2: Pretags 未找到，Danbooru 找到（基础信息）

**查询**: "某个新角色的信息"

**Agent 响应**:
```
⚠️ Pretags 中未找到，从 Danbooru 获取基础信息

📍 数据来源：Danbooru API

基本信息：
- 英文名：character_name
- 分类：角色 (Character)
- 出现次数：1,234 posts

相关标签：
1girl, long_hair, blue_eyes, school_uniform

⚠️ 注意：
- ❌ 无 LoRA 信息
- ❌ 无中文名称
- ❌ 无本地化数据（外观、服装细分）
- ✅ 可以直接使用英文标签

建议：
如果经常使用该角色，建议添加到 Pretags：
python modules/pretags-batch-import/scripts/add_character.py \
  --name "character_name" \
  --cname "中文名" \
  --source "来源作品"
```

### 场景 3: 两级都未找到

**查询**: "不存在的角色"

**Agent 响应**:
```
❌ 未找到角色

查询结果：
- Pretags：❌ 未找到
- Danbooru：❌ 未找到

建议：
1. 检查拼写（中文或英文名）
2. 尝试搜索系列名：
   python character_query.py --list-series
3. 如果是新角色，可以手动添加到 Pretags：
   python add_character.py --interactive
```

---

## 🔍 具体查询场景

### 1. 查询角色信息

**用户**: "折枝的信息是什么？"

**Agent 执行**:
```bash
# Step 1: 查询 Pretags
python modules/pretags-draw/scripts/pretags_manager.py search "折枝"

# 如果未找到，Step 2: 查询 Danbooru
python modules/danbooru-tag-scraper/scripts/danbooru.py character "zhezhi"
```

### 2. 查询标签

**用户**: "坐着的 tag 是什么？"

**Agent 执行**:
```bash
# Step 1: 查询 Pretags 动作类别
python modules/pretags-draw/scripts/pretags_manager.py search "坐着"

# 如果未找到，Step 2: 查询 Danbooru
python modules/danbooru-tag-scraper/scripts/danbooru.py tags --pattern "sitting*"
```

### 3. 查询画风

**用户**: "某个画风的信息"

**Agent 执行**:
```bash
# Step 1: 查询 Pretags 画风类别
python modules/pretags-draw/scripts/pretags_manager.py search "画风名"

# Danbooru 不适用（画风通常是 LoRA，不在 Danbooru）
```

---

## 🤖 Agent 约束

### 必须遵守的规则

1. **优先级严格** - 必须先查 Pretags，未找到才查 Danbooru
2. **标注数据源** - 明确告知数据来自 Pretags 还是 Danbooru
3. **区分信息完整度** - Pretags 数据标注为"完整"，Danbooru 标注为"基础"
4. **提供建议** - Danbooru 数据需建议用户添加到 Pretags
5. **处理失败** - 两级都未找到时，提供明确的建议

### 响应格式要求

**从 Pretags 获取**:
```
✅ 找到角色：XXX
📍 数据来源：Pretags（本地数据库）
[完整信息]
```

**从 Danbooru 获取**:
```
⚠️ Pretags 中未找到，从 Danbooru 获取基础信息
📍 数据来源：Danbooru API
[基础信息]
⚠️ 注意：无 LoRA、无中文、无本地化数据
建议：添加到 Pretags
```

**都未找到**:
```
❌ 未找到角色
查询结果：
- Pretags：❌ 未找到
- Danbooru：❌ 未找到
建议：[检查拼写/搜索系列/手动添加]
```

### 禁止的操作

- ❌ **跳过 Pretags 直接查 Danbooru** - 必须先查 Pretags
- ❌ **隐藏数据来源** - 必须明确标注来自 Pretags 还是 Danbooru
- ❌ **混淆信息完整度** - 不要把 Danbooru 基础信息说成完整信息
- ❌ **凭记忆回答** - 无论哪级查询都必须调用工具

---

## ⚙️ 环境要求

### Pretags 查询
- ✅ 无需代理
- ✅ 本地查询，极快
- ✅ 始终可用

### Danbooru 查询
- ⚠️ **需要代理**：`export HTTPS_PROXY=http://127.0.0.1:7890`
- ⚠️ 网络请求，较慢（1-3 秒）
- ⚠️ 速率限制（≥1 秒/请求）
- ⚠️ 可能失败（网络问题）

**代理检查**:
```bash
# 检查代理配置
echo $HTTPS_PROXY

# 测试 Danbooru 连接
curl -x $HTTPS_PROXY https://danbooru.donmai.us/tags.json?limit=1
```

---

## 📚 相关文档

- [Agent 查询指南](./AGENT_QUERY_GUIDE.md)
- [Pretags Draw](./modules/pretags-draw/SKILL.md)
- [Danbooru Tag Scraper](./modules/danbooru-tag-scraper/SKILL.md)
- [Pretags 数据管理](./references/pretags-data-management.md)

---

**最后更新**: 2026-06-08
