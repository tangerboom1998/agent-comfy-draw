# SKILL 文档标准模板

本文档定义 ComfyUI Draw 项目中所有 SKILL.md 文件的统一结构和编写规范。

---

## 📐 标准结构

每个 SKILL.md 必须包含以下章节，按顺序排列：

```markdown
---
name: module-name
description: "一句话描述（50-150字），说明模块功能、主要特性、适用场景"
version: x.y.z
metadata:
  nanobot:
    emoji: "🎨"
    requires:
      env: ["REQUIRED_ENV_VAR"]
  openclaw:
    emoji: "🎨"
    requires:
      env: ["REQUIRED_ENV_VAR"]
---

# Module Name

一段话（2-3句）概述模块的核心功能和用途。

## 🚀 快速开始

最简单的使用示例（3-10行代码），让用户立即上手。

## 🎯 核心功能

- 功能点 1 - 简短说明
- 功能点 2 - 简短说明
- 功能点 3 - 简短说明
- ...（3-8个功能点）

## ⚙️ 环境配置

**必需环境变量**:
- `VAR_NAME` - 说明用途和示例值

**可选环境变量**:
- `OPTIONAL_VAR` - 说明用途和默认值

**依赖**:
- Python 3.8+
- 必需的包列表

## 📖 使用示例

### 场景 1: 最常见的使用场景

简短描述场景。

\`\`\`bash
# 示例代码
command --arg value
\`\`\`

**说明**: 解释输出或效果。

### 场景 2: 第二常见场景

（重复上述结构）

## 📚 相关文档

- [详细指南](references/module-guide.md) - 深入说明
- [API 参考](references/module-api.md) - 完整 API 文档
- [故障排除](references/module-troubleshooting.md) - 常见问题

## 📄 许可证

MIT License
```

---

## ✅ 编写原则

### 1. 简洁性原则

- **目标长度**: 200-400 行
- **每个章节**: 不超过 50 行（除了使用示例）
- **描述**: 优先用简短的 bullet points，避免长段落
- **代码示例**: 只展示核心逻辑，省略样板代码

### 2. 清晰性原则

- 使用**主动语态**，避免被动语态
- 使用**现在时态**描述功能
- 使用**命令式**编写操作步骤
- 避免模糊词汇（"可能"、"大概"、"某些情况"）

**✅ 好的例子**:
```markdown
生成图片并保存到 output/ 目录。
```

**❌ 差的例子**:
```markdown
图片可能会被生成并且在某些情况下会保存到输出目录中。
```

### 3. 用户视角原则

- 从用户需求出发，不是从实现出发
- 先讲"怎么用"，不是"怎么实现"
- 技术细节归档到 references/

**✅ 好的例子**:
```markdown
### 下载模型

\`\`\`bash
python civitai.py download <model_id>
\`\`\`
```

**❌ 差的例子**:
```markdown
### 下载模型

本模块通过调用 Civitai API 的 /models endpoint，解析返回的 JSON，
提取 downloadUrl 字段，然后使用 requests.get() 流式下载文件到本地...
```

### 4. 无警告原则

- **限制**: 每个 SKILL.md 最多 3 条警告/注意事项
- **替代方案**: 
  - 将规则整合到正常流程中
  - 将限制转化为最佳实践
  - 将陷阱归档到 references/troubleshooting.md

**✅ 好的例子**:
```markdown
### LoRA 格式

LoRA 使用标准格式：

\`\`\`
<lora:model_name:strength>
\`\`\`

例如：`<lora:character_lora:0.8>`
```

**❌ 差的例子**:
```markdown
### LoRA 格式

⚠️ 注意：不要在 LoRA 名称后加 .safetensors 扩展名！
⚠️ 注意：不要在路径中包含子目录！
⚠️ 注意：必须使用 <lora:...> 格式，不能用其他格式！
⚠️ 注意：强度必须是 0-1 之间的小数！
...
```

### 5. 专业性原则

**禁止内容**:
- ❌ 个人化语言（"公子说"、"Agent 建议"）
- ❌ 时间戳（"2026-05-18 修正"）
- ❌ 调试日志和错误追踪
- ❌ 内部讨论和决策过程
- ❌ 情绪化表达（"太坑了"、"终于搞定"）

**鼓励内容**:
- ✅ 客观的功能描述
- ✅ 清晰的操作步骤
- ✅ 实用的示例代码
- ✅ 准确的技术术语

---

## 📋 章节详解

### Frontmatter（必需）

```yaml
---
name: module-name              # 模块标识符（小写，连字符）
description: "功能描述"         # 50-150字，说明核心功能
version: 1.0.0                 # 语义化版本号
metadata:                      # 元数据（可选）
  nanobot:
    emoji: "🎨"
    requires:
      env: ["ENV_VAR"]         # 必需的环境变量
---
```

### 标题和概述（必需）

```markdown
# Module Name

一段简短的概述（2-3句话），说明：
1. 这是什么
2. 解决什么问题
3. 主要特点
```

### 快速开始（必需）

```markdown
## 🚀 快速开始

最简单的使用方式，让用户在 1 分钟内运行起来。

\`\`\`bash
# 设置环境变量
export VAR=value

# 运行命令
python script.py
\`\`\`
```

**原则**:
- 代码必须可以直接复制运行
- 不需要额外的配置或准备
- 展示最核心的功能

### 核心功能（必需）

```markdown
## 🎯 核心功能

列出 3-8 个主要功能点，每个一行简短说明：

- **功能 1** - 一句话说明
- **功能 2** - 一句话说明
- **功能 3** - 一句话说明
```

### 环境配置（必需）

```markdown
## ⚙️ 环境配置

**必需**:
- `VAR_NAME` - 用途说明
  - 示例: `http://127.0.0.1:8188`

**可选**:
- `OPTIONAL_VAR` - 用途说明
  - 默认值: `default_value`

**依赖**:
- Python 3.8+
- requests>=2.31.0
```

### 使用示例（必需）

```markdown
## 📖 使用示例

### 场景 1: 场景描述

简短说明这个场景的用途。

\`\`\`bash
# 完整的可运行代码
command --flag value
\`\`\`

**输出**:
\`\`\`
预期的输出结果
\`\`\`

### 场景 2: 另一个场景

（重复上述结构）
```

**原则**:
- 展示 2-5 个常见场景
- 每个示例都完整可运行
- 包含输入和预期输出

### 相关文档（必需）

```markdown
## 📚 相关文档

- [详细指南](references/module-guide.md) - 完整功能说明
- [API 参考](references/module-api.md) - API 文档
- [故障排除](references/module-troubleshooting.md) - 常见问题
- [最佳实践](references/module-best-practices.md) - 使用建议
```

---

## 🚫 禁止的模式

### 1. 过度的技术细节

**❌ 不要在 SKILL 中写**:
```markdown
### 内部架构

节点 ID 映射表：
| 参数 | Node ID |
|------|---------|
| Prompt | 85 |
| Negative | 14 |
...（50行的映射表）
```

**✅ 应该**:
```markdown
### 工作流配置

工作流支持自定义参数配置。

详见：[节点配置指南](references/node-configuration.md)
```

### 2. 历史问题记录

**❌ 不要在 SKILL 中写**:
```markdown
**⚠️ 重要修正（2026-05-18）：**
之前 Agent 会把"折枝"理解成树枝，现在已经修复，必须先查 pretags...
```

**✅ 应该**:
```markdown
### 角色名识别

系统会自动查询 pretags 数据库识别角色名。

详见：[角色识别规则](references/character-identification.md)
```

### 3. 大量的警告堆叠

**❌ 不要在 SKILL 中写**:
```markdown
⚠️ 注意事项 1...
⚠️ 注意事项 2...
⚠️ 注意事项 3...
⚠️ 注意事项 4...
⚠️ 注意事项 5...
（10+ 条警告）
```

**✅ 应该**:
```markdown
## 使用注意

- 确保环境变量已配置
- LoRA 文件必须存在于指定目录

更多限制和最佳实践：[故障排除指南](references/troubleshooting.md)
```

---

## 📏 质量检查清单

在提交 SKILL.md 前，确认：

- [ ] 文件长度在 200-400 行之间
- [ ] 包含完整的 frontmatter
- [ ] 快速开始示例可以直接运行
- [ ] 警告/注意事项 ≤ 3 条
- [ ] 无个人化语言（"公子"、"Agent"）
- [ ] 无时间戳和历史记录
- [ ] 无内部实现细节
- [ ] 所有技术细节链接到 references/
- [ ] 代码示例都有注释
- [ ] 链接都可以访问
- [ ] 章节顺序符合标准
- [ ] 使用统一的 emoji 图标

---

## 🔗 相关文档

- [SKILL 审查报告](SKILL_AUDIT_REPORT.md) - 当前问题分析
- [references/ 组织规范](references/README.md) - 参考文档结构

---

**版本**: 1.0.0
**最后更新**: 2026-06-07
