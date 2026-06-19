# Agent 使用指南

Agent 使用本项目时的查询、绘图和响应规范。

---

## 一、角色和标签查询

### 查询优先级（严格遵守）

```
用户查询 → [Level 1] Pretags 本地数据库 → 找到？→ 返回完整信息
                                             ↓ 未找到
                              [Level 2] Danbooru API → 找到？→ 返回基础信息
                                                             ↓ 未找到
                                                      告知未找到，建议手动添加
```

| 特性 | Level 1: Pretags | Level 2: Danbooru |
|------|-----------------|-------------------|
| 数据来源 | 本地 pretags.json | Danbooru API |
| 响应速度 | 极快 | 慢（2-3秒） |
| 信息完整度 | 完整（LoRA、权重、中文） | 基础（英文 tag） |
| LoRA / 中文名 | 有 | 无 |
| 需要代理 | 否 | 是（`HTTPS_PROXY`） |

### 查询工具

**pretags_manager.py**（主查询工具）：
```bash
# 列出所有类别
python modules/pretags-draw/scripts/pretags_manager.py list
# 搜索角色/标签（可选指定类别）
python modules/pretags-draw/scripts/pretags_manager.py search "折枝"
python modules/pretags-draw/scripts/pretags_manager.py search "坐着" 服装
# 查看条目详情（需 <类别> <条目名>）
python modules/pretags-draw/scripts/pretags_manager.py info 人物 "折枝"
# 统计信息
python modules/pretags-draw/scripts/pretags_manager.py stats
```

**character_query.py**（角色专用）：
```bash
python modules/pretags-draw/scripts/character_query.py "折枝"
python modules/pretags-draw/scripts/character_query.py --series "鸣潮"
python modules/pretags-draw/scripts/character_query.py --list-series
```

**Danbooru API**（备选，需代理）：
```bash
export HTTPS_PROXY=http://127.0.0.1:7890
python modules/danbooru-tag-scraper/scripts/danbooru.py char-info --tag "zhezhi_(wuthering_waves)"
python modules/danbooru-tag-scraper/scripts/danbooru.py tags --pattern "*_hair" --category 0 --min-posts 500
```

### 响应格式

**Pretags 找到（完整信息）**：
```
✅ 找到角色：折枝（zhezhi）
📍 数据来源：Pretags（本地数据库）

基本信息：
- 中文名：折枝 / 英文名：zhezhi / 来源：鸣潮
- LoRA：✅ 有（zhezhi-anima，权重 0.9/0.9）

外观特征：long hair, blue eyes, blue dress, white sleeves
常用标签：1girl, long_hair, blue_dress

使用方法：tag_producer 输入"折枝 服装 外貌 0.9"
```

**Danbooru 找到（基础信息）**：
```
⚠️ Pretags 中未找到，从 Danbooru 获取基础信息
📍 数据来源：Danbooru API

- 英文名：character_name
- 分类：角色 (Character) / 出现次数：1,234 posts
- 相关标签：1girl, long_hair, blue_eyes

⚠️ 无 LoRA、无中文、无本地化数据
建议：如果经常使用，添加到 Pretags 以获取完整功能
```

**都未找到**：
```
❌ 未找到角色
- Pretags：❌ 未找到
- Danbooru：❌ 未找到
建议：检查拼写或手动添加到 Pretags
```

### 查询规则

- 不得跳过 Pretags 直接查 Danbooru
- 必须标注数据来源和信息完整度
- 不得凭记忆回答，必须调用工具
- 找到多个同名角色时，提示用户指定系列

---

## 二、绘图工作流

绘图工作流完整规则见 [Pretags Draw](../modules/pretags-draw/SKILL.md)。核心路径：

```
用户需求 → 构建中文指令 → tag_producer → 生成英文 prompt + LoRA → comfyui_draw.py 生图
```

中文指令格式：`<角色名> [服装] [外貌] [权重] [动作/类别/画师...]`，示例 `"折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 0.7 撸串 4"`。

```bash
python modules/pretags-draw/scripts/tag_producer.py "折枝 服装 外貌 0.9 动作 坐着 画风 2d润彩 0.7 撸串 4"
# → 输出含 LoRA 的完整 prompt，直接传给 comfyui_draw.py
```

tag_producer 输出示例：
```
masterpiece, best quality, solo,
<lora:zhezhi-anima:0.9:0.9>,
zhezhi, 1girl, long hair, blue eyes, blue dress, white sleeves,
sitting, on chair,
<lora:jijia-gnoobv-000014:0.7:0.7>,
wlop, ask, fu_mi, sakimichan
```

如有中文残留，Agent 翻译为英文并按层级重组，执行质量检查（零中文、画质前缀、主体/服装/表情/姿势描述、权重合理）。

### 模型提示词差异

| 模型 | 格式 | 画师格式 | 语言 |
|------|------|---------|------|
| **Anima (Flux)** | tag + 短句 | 加 @：`@wlop` | 仅英文 |
| **SDXL (Illustrious/Noob)** | 纯 tag 最佳 | 不加 @：`wlop` | 仅英文 |
| **z-image Turbo** | 自然语言 | — | 中英文均可 |

LoRA 格式：`<lora:LoRA文件名:unet权重:text权重(可选)>`，文件名不带 `.safetensors`。详见 [模型提示词对比](model-prompt-comparison.md)。

---

## 三、Agent 约束总结

Agent 行为约束见根 [SKILL.md](../SKILL.md) 的 frontmatter `agent_constraints`。本指南聚焦查询与绘图的关键纪律：

- 查询优先级：Pretags → Danbooru，不得跳过，必须标注数据来源和信息完整度
- 不得凭记忆回答，必须调用工具
- 生图必须使用 tag_producer 统一管线，不得跳过或拆分调用（不单独 `pretags_manager.py search` 后自行拼 prompt，也不跳过 pretags 查询凭记忆构建）
