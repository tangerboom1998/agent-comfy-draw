---
name: comfyui-draw-suite
description: "AI绘画工具套件：ComfyUI 工作流引擎 + Pretags 标签管理系统 + Civitai 模型集成 + Web 可视化界面。支持 19,000+ 角色库、10,000+ 标签库、中文提示词自动转换、LoRA 管理、画风测试、批量生成。"
version: 2.0.0
metadata:
  nanobot:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
  openclaw:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
agent_constraints:
  forbidden:
    - "修改任何 SKILL.md 文档（未经用户明确允许）"
    - "修改项目代码文件（未经用户明确允许）"
    - "删除或重命名现有文件"
  allowed:
    - "根据用户习惯新增 reference 文档（需遵循 REFERENCE_TEMPLATE.md，保持简洁 ≤150 行）"
    - "向 [WARNINGS.md](references/warnings.md) 添加新的警告或提醒"
    - "创建临时分析报告（*_REPORT.md, *_AUDIT.md）"
    - "回答问题和提供建议"
---

# ComfyUI Draw Suite

完整的 AI 绘画工具套件，提供从模型管理、标签系统、提示词处理到图片生成的端到端解决方案。

## 🤖 Agent 使用规范

**使用本项目时，Agent 必须遵守以下约束**：

### 禁止操作（未经用户明确允许）
- ❌ 修改任何 SKILL.md 文档
- ❌ 修改项目代码文件
- ❌ 删除或重命名现有文件
- ❌ 修改 Git 配置

### 允许操作
- ✅ 根据用户习惯新增 reference 文档（需遵循 [REFERENCE_TEMPLATE.md](REFERENCE_TEMPLATE.md)，保持简洁 ≤150 行）
- ✅ 向 [WARNINGS.md](references/warnings.md) 添加新的警告或提醒
- ✅ 创建临时分析报告（`*_REPORT.md`, `*_AUDIT.md`）
- ✅ 回答问题和提供建议

### ⚠️ 核心原则：必须使用 CLI，禁止自己写代码

**Agent 使用本项目时，必须优先使用项目提供的 CLI 脚本和模块，禁止自行编写生图、查询或数据处理代码。**

具体要求：

1. **生图必须用 `comfyui_draw.py`** — 禁止自己写 requests/aiohttp 调 ComfyUI API，禁止复制 `test_anima.py` 的硬编码写法
2. **查询必须用 `pretags_manager.py`** — 禁止自己解析 pretags JSON 文件
3. **标签处理必须用 `tag_producer.py`** — 禁止自己拼装英文 tag
4. **必须根据模型类型选择工作流** — 生图时必须通过 `--workflow` 参数指定工作流（`anima`/`noob`/`zimage`），由 Agent 根据用户需求决定使用哪个工作流，不要依赖默认值
5. **先完整扫描技能模块再行动** — 使用任何功能前，必须先查看对应模块的 `SKILL.md`、`scripts/` 目录和 `assets/` 目录，确认已有的 CLI 和 API，不要跳过发现步骤直接动手

> 如果发现现有 CLI 不满足需求，应先告知用户并讨论方案，而非自行编写代码。

### 绘图工作流约束

**当用户要求生图时，必须遵循 pretags-draw 工作流**：

1. **必须使用 tag_producer** - 不要跳过 tag_producer 直接构建英文 prompt
2. **从 pretags 获取数据** - 角色信息、LoRA、画风等必须从 pretags 数据库查询
3. **遵循标准流程** - 用户需求 → 中文指令 → tag_producer → comfyui_draw.py
4. **根据模型调整提示词** - 必须根据使用的模型类型（Anima/SDXL/z-image）调整提示词格式

> ⚠️ **tag_producer 完整调用规则（严格遵守）**
>
> tag_producer 是一个**不可拆分的统一管线**：它同时完成 pretags 数据查询（角色/画风/LoRA 信息检索）和提示词生成（英文 tag + LoRA 格式拼接）。使用 pretags 相关功能获取提示词时，**必须走 tag_producer 的完整调用流程**，禁止以下两种行为：
>
> - ❌ **只查询 pretags 数据不走 tag_producer 生成提示词** — 不要单独调用 pretags_manager.py search 获取角色信息后，自行拼接英文 prompt；必须将中文指令交给 tag_producer 一次性处理
> - ❌ **只拼接提示词不经过 pretags 查询** — 不要跳过 tag_producer 直接用记忆或手动查询结果构建英文 prompt；tag_producer 会从 pretags 数据库实时检索最新数据
>
> 正确做法：将完整中文指令传给 `python tag_producer.py "<中文指令>"`，由它统一完成数据查询 + 提示词生成，输出可直接传给 comfyui_draw.py 的完整 prompt。

### 角色和标签查询约束

**当用户查询角色信息或标签时，必须使用两级查询系统**：

#### 查询优先级（严格遵守）

1. **Level 1: Pretags（优先）**
   - 本地查询，极快
   - 完整信息：LoRA、权重、中文名、外观、服装
   - 工具：`pretags_manager.py search <角色名>`

2. **Level 2: Danbooru（备选）**
   - 仅当 Pretags 未找到时使用
   - 基础信息：英文标签、分类
   - 需要代理：`HTTPS_PROXY=http://127.0.0.1:7890`
   - 工具：`danbooru.py character <角色名>`

#### 响应格式要求

**从 Pretags 获取时**：
```
✅ 找到角色：XXX
📍 数据来源：Pretags（本地数据库）
[显示完整信息：LoRA、权重、标签]
```

**从 Danbooru 获取时**：
```
⚠️ Pretags 中未找到，从 Danbooru 获取基础信息
📍 数据来源：Danbooru API
[显示基础信息]
⚠️ 注意：无 LoRA、无中文、无本地化数据
建议：添加到 Pretags 以获取完整功能
```

**都未找到时**：
```
❌ 未找到角色
- Pretags：❌ 未找到
- Danbooru：❌ 未找到
建议：检查拼写或手动添加
```

#### 禁止操作
- ❌ 跳过 Pretags 直接查 Danbooru
- ❌ 隐藏数据来源
- ❌ 混淆信息完整度
- ❌ 凭记忆回答

详见：[Agent 使用指南](references/agent-guide.md)

#### 模型特性差异（必须遵守）

**Anima (Flux)**:
- ✅ 可用 tag + 短句：`a girl with long hair, 1girl, solo`
- ✅ 画师加 @：`@wlop`, `@big chungus`
- ✅ 添加：`newest, latest, safe`
- ✅ 仅英文，有语义理解

**SDXL (Illustrious/Noob)**:
- ✅ 纯 tag 最佳：`1girl, solo, long_hair, silver_hair`
- ✅ 画师不加 @：`wlop`, `big_chungus`
- ✅ 支持 LoRA：`<lora:xxx:0.8:0.8>`（格式见下方规范）
- ✅ 仅英文，弱语义

**z-image Turbo**:
- ✅ 自然语言：`一个银发红瞳的女孩穿着白裙子`
- ✅ 支持中英文
- ✅ 强语义理解
- ✅ 参数：Steps=4, CFG=1.0

详见：
- [Pretags Draw 工作流](modules/pretags-draw/SKILL.md#-agent-工作流约束)
- [Agent 使用指南](references/agent-guide.md)
- [模型提示词对比](references/model-prompt-comparison.md)
- **LoRA 格式规范**：`<lora:LoRA文件名:unet权重:text权重(可选)>`，如 `<lora:jijia-anima-Tanger:0.8>` 或 `<lora:jijia-anima-Tanger:0.8:0.8>`。文件名不带 `.safetensors` 扩展名和目录路径

## 🎯 功能唤醒：意图 → 模块映射

**当用户表达以下意图时，Agent 必须按"模块"列路由到对应模块执行，禁止自行实现。**

| 用户意图 | 模块 | 入口 CLI / 工具 | 说明 |
|---------|------|----------------|------|
| 画图 / 生图 / 生成图片 | `modules/pretags-draw` | `comfyui_draw.py --workflow <类型>` | 必须通过 `--workflow` 指定工作流 |
| roll 提示词 / 随机画师 / 撸串 | `modules/pretags-draw` | `tag_producer.py "撸串 4"` | 画师随机抽取 + pretags 预设标签组合 |
| 用中文描述生图 / 角色+动作+画风 | `modules/pretags-draw` | `tag_producer.py "角色 服装 外貌 动作 画风 撸串 N"` | 中文指令 → 英文 tag + LoRA 完整 prompt |
| 查角色信息 / 查标签 | `modules/pretags-draw` | `pretags_manager.py search "关键词"` | 优先 Pretags，未命中转 Danbooru |
| 找某个角色的提示词 | `modules/pretags-draw` → `modules/danbooru-tag-scraper` | `pretags_manager.py search` → `danbooru.py character` | 两级查询：先 Pretags，未找到转 Danbooru |
| 画图找找灵感 / 参考图打标 | `modules/prompt_inspiration` | `prompt_inspiration search` / `prompt_inspiration tag` | 语义搜索打标库 / 图片自动打标 |
| 解析图像提取提示词 | `modules/prompt_inspiration` | `prompt_inspiration inspect <图片>` | 优先从元数据提取，无元数据回退视觉分析 |
| 管理 Pretags 数据 / 编辑角色标签 | `modules/pretags-draw` + Tanger-Presets-Show | `pretags_manager.py` + `server.py` | CLI 增删改查 + Web 可视化编辑 |
| 构筑 / 编辑 ComfyUI 工作流 | `modules/comfyui-api` | `extract_schema.py` / `run_workflow.py` | 工作流 Schema 提取和执行 |
| 下载模型 / 从 Civitai 获取 | `modules/civitai-api` | `civitai.py search` / `civitai.py download` | 模型搜索、下载、hash 查询 |
| 搜索模型 / 找模型 | `modules/civitai-api` | `civitai.py search "关键词"` | 按名称/类型搜索 Civitai 模型 |
| 画风测试 / 批量测试画风 | `tools/artstyle-test` | `artstyle_test.py [画风名]` | 多维测试 + 视觉分析 + 描述生成 |
| 批量导入 / 导入 Pretags 数据 | `tools/pretags-batch-import` | 批量导入脚本 | Excel/JSON 数据批量导入 |
| 启动 ComfyUI | `tools/comfyui-startup` | 启动脚本 | ComfyUI 服务启动和环境管理 |

> **路由原则**：Agent 识别到上述意图后，先读取对应模块的 `SKILL.md`，再按其 CLI 规范执行。禁止跳过模块直接自行编码。

## 🚀 快速开始

```bash
# 1. 初始化项目
./setup.sh

# 2. 配置环境变量
export COMFYUI_HOST=http://127.0.0.1:8188

# 3. 启动 Web 管理界面
cd modules/Tanger-Presets-Show && python3 server.py
# 访问 http://localhost:8765

# 4. 生成图片（必须指定工作流）
cd modules/pretags-draw/scripts
python comfyui_draw.py "masterpiece, best quality, 1girl, smile" --workflow anima --canvas 竖图
```

## 🎯 核心功能

- **AI 绘图工作流** - 支持 Noob/Anima/z-image 三种工作流，Agent 根据需求选择
- **Pretags 标签管理** - 19,000+ 角色和 10,000+ 标签的结构化数据库
- **中文提示词引擎** - 自动将中文关键词转换为 SDXL 英文标签
- **Web 可视化界面** - Tanger-Presets-Show 提供可视化标签管理
- **模型管理** - Civitai 模型搜索、下载和自动部署
- **批量处理** - 画风测试、预览图生成、数据导入

## 📦 模块说明

### 核心模块 (`modules/`)

#### ComfyUI API
ComfyUI 官方 API 封装，负责工作流执行和生命周期管理。

**文档**: [comfyui-api/SKILL.md](modules/comfyui-api/SKILL.md)
**环境变量**: `COMFYUI_HOST` (必需)

#### Pretags Draw
主绘图工作流，整合中文提示词引擎和 ComfyUI 生图。

**文档**: [pretags-draw/SKILL.md](modules/pretags-draw/SKILL.md)
**环境变量**: `COMFYUI_HOST` (必需)

#### Tanger-Presets-Show
Pretags 数据的 Web 可视化管理界面，支持卡片浏览、搜索、编辑。

**文档**: [Tanger-Presets-Show/README.md](modules/Tanger-Presets-Show/README.md)
**启动**: `cd modules/Tanger-Presets-Show && python3 server.py`

#### Civitai API
Civitai 模型搜索、下载、hash 查询和 Vault 管理。

**文档**: [civitai-api/SKILL.md](modules/civitai-api/SKILL.md)
**环境变量**: `CIVITAI_API_KEY` (可选)

#### Danbooru Tag Scraper
Danbooru 标签爬取工具，按类别批量获取标签构建词典。

**文档**: [danbooru-tag-scraper/SKILL.md](modules/danbooru-tag-scraper/SKILL.md)
**环境变量**: `HTTPS_PROXY` (必需)

#### Prompt Inspiration
打标数据灵感检索 + 图片自动打标工具，支持语义搜索和 VLM/WD 双引擎打标。

**文档**: [prompt_inspiration/SKILL.md](modules/prompt_inspiration/SKILL.md)
**环境变量**: `HTTPS_PROXY` (VLM/模型下载), `VLM_API_KEY` (VLM 调用)

### 辅助工具 (`tools/`)

#### 画风测试
批量测试画风 LoRA 效果。

**文档**: [artstyle-test/SKILL.md](tools/artstyle-test/SKILL.md)

#### 批量导入
Pretags 数据批量导入和修复工具。

**文档**: [pretags-batch-import/SKILL.md](tools/pretags-batch-import/SKILL.md)

#### ComfyUI 启动
ComfyUI 启动脚本和环境管理。

**文档**: [comfyui-startup/SKILL.md](tools/comfyui-startup/SKILL.md)

## ⚙️ 环境配置

### 必需环境变量

```bash
# ComfyUI 服务地址
COMFYUI_HOST=http://127.0.0.1:8188
```

### 可选环境变量

```bash
# Civitai API 密钥（模型下载需要）
CIVITAI_API_KEY=your_api_key_here

# Pretags 数据文件路径
PRETAGS_DATA_PATH=./pretags/pretags-anima.json

# 图片输出目录（所有脚本统一使用，避免输出到各模块自身的 output/ 子目录）
COMFYUI_OUTPUT_DIR=./output

# Tanger-Presets-Show 端口
WEB_SHOW_PORT=8765

# LoRA 模型目录
LORA_MODEL_DIR=/path/to/models/loras

# 代理配置（Civitai 下载和 Danbooru 访问）
HTTP_PROXY=http://proxy.example.com:2090
HTTPS_PROXY=http://proxy.example.com:2090
```

### 依赖安装

```bash
# 安装所有依赖
pip install -r requirements.txt

# 或手动安装核心依赖
pip install websocket-client requests python-dotenv pillow openpyxl pandas aiohttp
```

## 📖 使用示例

### 场景 1: 生成单张图片

```bash
cd modules/pretags-draw/scripts
python comfyui_draw.py "masterpiece, best quality, 1girl, blue eyes, long hair, smile" \
  --workflow noob --canvas 竖图 --steps 28 --cfg 7.0
```

### 场景 2: 使用中文提示词

```bash
# tag_producer 自动处理中文指令
python tag_producer.py "折枝 服装 外貌 动作 坐着 画风 2d润彩 撸串 3"
```

### 场景 3: 批量生成角色预览图

```bash
cd modules/pretags-draw/scripts
python gen_character_previews.py --batch --canvas 方图 --steps 20
```

### 场景 4: 管理 Pretags 数据

```bash
# 启动 Web 界面
cd modules/Tanger-Presets-Show
python server.py

# 访问 http://localhost:8765
# 可视化浏览、搜索、编辑角色和标签
```

### 场景 5: 下载 Civitai 模型

```bash
cd modules/civitai-api/scripts
python civitai.py search "character name"
python civitai.py download <model_id>
```

## 🏗️ 工作流类型

项目支持三种 ComfyUI 工作流，根据文件名自动识别：

| 工作流 | 文件名 | 模型架构 | 适用场景 |
|--------|--------|---------|---------|
| **Noob** | `noob_*` | SDXL | 通用插画生成 |
| **Anima** | `anima_*` | Flux | 高质量角色生成 |
| **z-image** | `z_image_*` | Flux | 快速草图生成 |

详细的节点映射和架构说明：[工作流节点映射](references/workflow-node-mapping.md)

## 📊 数据文件

### Pretags 数据

**位置**: `pretags/` 目录
- `pretags-anima.json` (19MB) - Anima 工作流数据
- `pretags-ill-noob.json` (20MB) - Illustrious/Noob 工作流数据

**结构**: ID-key 格式（自 2026-05-20）
- 19,000+ 角色定义
- 10,000+ 标签分类
- LoRA 关联信息

**文档**: [Pretags 数据管理](references/pretags-data-management.md)

### 数据文件管理

数据文件通过智能路径解析自动加载：

1. CLI 参数 `--pretags-path`（最高优先级）
2. 环境变量 `PRETAGS_DATA_PATH`（推荐配置）
3. 项目根目录 `pretags/` 目录（自动发现）

详见：[数据文件管理指南](references/data-management.md)

## 📚 文档索引

### 模块文档
- [ComfyUI API](modules/comfyui-api/SKILL.md)
- [Pretags Draw](modules/pretags-draw/SKILL.md)
- [Civitai API](modules/civitai-api/SKILL.md)
- [Danbooru Tag Scraper](modules/danbooru-tag-scraper/SKILL.md)
- [Prompt Inspiration](modules/prompt_inspiration/SKILL.md)
- [Tanger-Presets-Show](modules/Tanger-Presets-Show/README.md)

### 工具文档
- [画风测试](tools/artstyle-test/SKILL.md)
- [批量导入](tools/pretags-batch-import/SKILL.md)
- [ComfyUI 启动](tools/comfyui-startup/SKILL.md)

### 参考文档
- [警告和注意事项](references/warnings.md)
- [Agent 使用指南](references/agent-guide.md)
- [Anima Prompt 与工作流](references/anima-prompt-and-workflow.md)
- [z-image Turbo 工作流](references/z-image-guide.md)
- [工作流节点映射](references/workflow-node-mapping.md)
- [Pretags Draw 使用规则](references/pretags-draw-rules.md)
- [画风管理与测试](references/artstyle-curation.md)
- [角色预览图生成](references/character-preview-generation.md)
- [Pretags 数据管理](references/pretags-data-management.md)
- [数据文件管理](references/data-management.md)
- [Pretags Excel 导入导出](references/pretags-excel-workflow.md)
- [ComfyUI 常见问题](references/comfyui-pitfalls.md)
- [环境配置](references/environment-setup.md)
- [发布检查清单](references/release-checklist.md)

### 用户个性化参考 (`user-references/`)

**该目录用于存放用户个性化的设置、模板和经验记录，不受 Git 版本控制。**

Agent 在处理用户请求时，应优先检查此目录中的个性化配置。

**结构**：
```
user-references/
├── README.md                # 索引文件（列出所有用户文档）
├── user-preferences.md      # 用户偏好设置（常用画风、默认参数等）
├── prompt-templates.md      # 用户自定义提示词模板
├── workflow-notes.md        # 工作流调优经验
└── character-favorites.md   # 常用角色速查
```

**使用规则**：
- ✅ Agent 可读取并遵循用户的个性化配置
- ✅ Agent 可根据用户要求新增或修改此目录中的文档
- ✅ 此目录已在 `.gitignore` 中排除，不会影响仓库
- ❌ Agent 不应主动删除用户的个性化文档

详见：[user-references/README.md](user-references/README.md)

## 📄 许可证

MIT License
