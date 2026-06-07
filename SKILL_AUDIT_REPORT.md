# SKILL 文档审查报告

**审查日期**: 2026-06-07
**审查范围**: 所有 8 个 SKILL.md 文件

---

## 📊 文档概览

| 文件 | 行数 | 警告数 | 状态 | 主要问题 |
|------|------|--------|------|----------|
| `./SKILL.md` | 373 | 7 | ⚠️ 需重构 | 技术细节过多、节点ID映射应归档 |
| `modules/pretags-draw/SKILL.md` | 632 | 33 | ❌ 严重 | 大量警告、重复内容、历史修正混杂 |
| `modules/comfyui-api/SKILL.md` | 606 | ? | ✅ 较好 | 结构清晰，但可能过于详细 |
| `modules/civitai-api/SKILL.md` | 244 | ? | ✅ 较好 | 长度适中 |
| `modules/danbooru-tag-scraper/SKILL.md` | ? | ? | 待审查 | - |
| `tools/artstyle-test/SKILL.md` | ? | ? | 待审查 | - |
| `tools/comfyui-startup/SKILL.md` | ? | ? | 待审查 | - |
| `tools/pretags-batch-import/SKILL.md` | ? | ? | 待审查 | - |

---

## 🔍 主要问题分类

### 1. **过度的技术细节**（应归档到 reference）

#### 主 SKILL.md
```markdown
### 节点ID映射

| 参数 | Noob (node ID) | Anima (node ID) | z-image (node ID) |
|------|---------------|-----------------|-------------------|
| Prompt | 85 | 10 | 31 |
| Negative | 14 | 37 | 7 |
...
```
**问题**: 节点ID映射是实现细节，不应在主SKILL中
**建议**: 移至 `references/workflow-node-mapping.md`

#### 主 SKILL.md
```markdown
### Hires.fix 放大架构

Noob:   KSampler[48] → UltimateSDUpscale[94] ...
Anima:  KSamplerAdv[30] → LatentUpscaleBy[55] ...
```
**问题**: 工作流内部架构，普通用户不需要知道
**建议**: 移至 `references/workflow-architecture.md`

---

### 2. **过多的警告和注意事项**

#### pretags-draw/SKILL.md (33处警告)

**示例问题**:
```markdown
**⚠️ 角色名歧义识别规则（公子纠正 2026-05-18）：**
- 当公子说出中文角色名（如「折枝」「铃」「哲」「柳」），**必须先查 pretags 确认**
- 不要凭字面意思理解（「折枝」不是树枝，是鸣潮角色）
```

**问题**:
1. 个人化内容（"公子纠正"）不应出现在文档中
2. 特定场景的修正应该是系统行为，不是警告
3. 时间戳（2026-05-18）表明这是历史修正记录

**建议**:
- 移除个人化语言
- 将规则整合到正常流程描述中
- 历史修正记录归档到 `references/changelog-pretags-draw.md`

---

### 3. **历史问题和修正记录混杂**

#### pretags-draw/SKILL.md
```markdown
**⚠️ `solo` tag 规则（防止重影/多人物鬼影，公子纠正 2026-05-18）：**
- 所有单角色生图（1girl/1boy/1other）**必须加 `solo` tag**
- 不加 `solo` 时 noobaiXL 模型容易出现重影...
```

**问题**: 这是一个已知问题的修复，不应作为警告存在

**正确做法**:
```markdown
### 单角色绘图

单角色绘图时需要添加 `solo` 标签：

```python
prompt = f"masterpiece, best quality, solo, {character}, 1girl, ..."
```

这可以防止模型生成多个人物或重影。
```

---

### 4. **结构不一致**

各个 SKILL.md 的结构差异很大：

- `comfyui-api/SKILL.md`: 有明确的 frontmatter + reference docs 说明
- `pretags-draw/SKILL.md`: 没有清晰的章节分隔，内容混杂
- 主 `SKILL.md`: 介于两者之间

---

## 📋 标准化建议

### SKILL.md 应该包含什么

✅ **应该有**:
1. **frontmatter** - 元数据（name, description, version等）
2. **概述** - 一段话说明模块功能
3. **快速开始** - 最简单的使用示例（3-5行代码）
4. **核心功能** - 列出主要功能点（bullet points）
5. **环境要求** - 必需的环境变量和依赖
6. **使用示例** - 常见场景的完整示例
7. **相关文档** - 链接到 references/ 中的详细文档

❌ **不应该有**:
1. 详细的节点ID映射表
2. 内部实现细节（如工作流节点连接图）
3. 大量的警告和注意事项（>5条）
4. 历史修正记录和时间戳
5. 个人化语言（"公子说"、"Agent修正"）
6. 故障排除指南（应在 TROUBLESHOOTING.md）
7. 详细的API参考（应在 references/）

---

### references/ 应该包含什么

✅ **应该归档**:
1. **技术细节** - workflow-node-mapping.md, workflow-architecture.md
2. **故障排除** - workflow-pitfalls.md（已有 comfyui-pitfalls.md）
3. **历史记录** - changelog-{module}.md
4. **深入指南** - {topic}-deep-dive.md
5. **最佳实践** - {topic}-best-practices.md

---

## 🎯 重构计划

### 阶段 1：制定标准模板（Task #6）

创建 `SKILL_TEMPLATE.md`:
```markdown
---
name: module-name
description: "一句话描述模块功能"
version: x.y.z
metadata:
  nanobot:
    emoji: "🎨"
    requires:
      env: ["ENV_VAR"]
---

# Module Name

一段话概述模块功能和用途。

## 🚀 快速开始

\`\`\`bash
# 最简单的使用示例
command example
\`\`\`

## 🎯 核心功能

- 功能点 1
- 功能点 2
- 功能点 3

## ⚙️ 环境要求

**必需**:
- `ENV_VAR` - 说明

**可选**:
- `OPTIONAL_VAR` - 说明

## 📖 使用示例

### 场景 1: 描述

\`\`\`bash
示例代码
\`\`\`

### 场景 2: 描述

\`\`\`bash
示例代码
\`\`\`

## 📚 相关文档

- [详细指南](references/module-guide.md)
- [API参考](references/module-api.md)
- [故障排除](references/module-troubleshooting.md)
```

---

### 阶段 2：内容归档（准备工作）

#### 需要创建的 reference 文档

1. **workflow-node-mapping.md**
   - 从主 SKILL.md 移动节点ID映射表
   - 从主 SKILL.md 移动 Hires.fix 架构图

2. **workflow-architecture.md**
   - 三种工作流的详细架构
   - 节点连接图
   - 放大管线说明

3. **pretags-draw-rules.md**
   - 整合所有的"规则"和"注意事项"
   - 移除个人化语言
   - 按主题组织

4. **pretags-draw-changelog.md**
   - 所有带时间戳的修正记录
   - "公子纠正"等历史问题

5. **lora-format-guide.md**
   - LoRA 格式规范
   - 常见错误和解决方案

---

### 阶段 3：重写 SKILL 文档（Task #7）

按优先级重写：

**高优先级**:
1. `modules/pretags-draw/SKILL.md` - 问题最严重
2. `./SKILL.md` - 主文档，影响最大

**中优先级**:
3. `modules/comfyui-api/SKILL.md` - 基本良好，需要精简
4. `modules/civitai-api/SKILL.md` - 基本良好，需要统一格式

**低优先级**:
5-8. tools/ 下的 SKILL.md - 后续统一格式

---

## 📝 具体修改示例

### Before (pretags-draw/SKILL.md)

```markdown
**⚠️ 角色名歧义识别规则（公子纠正 2026-05-18）：**
- 当公子说出中文角色名（如「折枝」「铃」「哲」「柳」），**必须先查 pretags 确认**
- 不要凭字面意思理解（「折枝」不是树枝，是鸣潮角色）
- 快速判断：`python scripts/pretags_manager.py search <关键词>`
- 如果搜索结果中有来源标识（鸣潮/绝区零/原神/崩坏等），按角色处理
- 如果不确定，问公子确认
```

### After (简洁版)

```markdown
### 角色名处理

当用户提供中文角色名时，使用 pretags 数据库查询：

\`\`\`bash
python scripts/pretags_manager.py search <角色名>
\`\`\`

如果搜索结果包含来源信息（如"鸣潮"、"原神"），将其识别为角色。

详见：[角色识别规则](references/character-identification.md)
```

---

## ⏱️ 预估工作量

| 任务 | 预估时间 |
|------|----------|
| 制定标准模板 | 30分钟 |
| 创建 5 个 reference 文档 | 2小时 |
| 重写 pretags-draw/SKILL.md | 1.5小时 |
| 重写主 SKILL.md | 1小时 |
| 优化其他 6 个 SKILL.md | 2小时 |
| **总计** | **7小时** |

---

## ✅ 验收标准

重构完成后，每个 SKILL.md 应满足：

1. ✅ 长度控制在 200-400 行
2. ✅ 警告和注意事项 ≤ 3 条
3. ✅ 无个人化语言（"公子"、"Agent"）
4. ✅ 无时间戳和历史修正记录
5. ✅ 遵循统一的章节结构
6. ✅ 所有技术细节链接到 references/
7. ✅ 快速开始示例清晰简洁
8. ✅ frontmatter 完整准确

---

**审查人**: Claude Code Assistant
**下一步**: 开始任务 #6 - 制定 SKILL 文档标准模板
