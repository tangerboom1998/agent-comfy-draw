---
name: comfyui-draw-suite
description: "AI绘画工具套件：ComfyUI工作流引擎 + Pretags标签管理系统 + Civitai模型集成 + Web可视化界面。支持19,000+角色库、10,000+标签库、中文提示词自动转换、LoRA管理、画风测试、批量生成。支持多工作流类型(Noob/Anima/z-image)自动检测。"
version: 1.1.0
metadata:
  nanobot:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
  openclaw:
    emoji: "🎨"
    requires:
      env: ["COMFYUI_HOST"]
---

# ComfyUI Draw Suite

AI绘画工具套件，提供完整的AI图片生成工作流、标签管理系统和模型下载功能。

## 🎯 核心功能

- **AI绘图工作流**：通过ComfyUI API生成高质量AI图片，支持Noob/Anima/z-image三种工作流类型
- **多工作流自动检测**：`comfyui_client.py`根据文件名自动识别工作流类型，分配正确的节点ID映射
- **Hires.fix 放大**：Anima/z-image工作流内置LatentUpscaleBy+二次KSampler放大管线，默认关闭
- **Pretags标签管理**：19,000+角色和10,000+标签的结构化数据库
- **中文提示词引擎**：自动将中文关键词转换为SDXL英文tag
- **Web可视化界面**：Tanger-Presets-Show - 可视化标签管理和预览
- **模型管理**：Civitai模型搜索、下载和自动部署
- **批量处理**：画风测试、预览图生成、数据导入

## 📦 模块说明

### 🎯 主要功能模块（`modules/`）

这些是 ComfyUI Draw 的核心功能模块，各自负责一个独立的领域。

#### [`civitai-api/`](modules/civitai-api/SKILL.md)
Civitai 公共 REST API 完整封装，支持模型搜索、下载、hash 查询、vault 管理等 21 个子命令。负责模型元数据获取和下载，是 pretags 数据入库的前置步骤。

**核心功能**：
- 模型搜索和下载
- Hash 批量查询
- ComfyUI 自动部署
- Vault 管理

**环境变量**：`CIVITAI_API_KEY`（可选，NSFW 内容和下载需要）

#### [`comfyui-api/`](modules/comfyui-api/SKILL.md)
ComfyUI 官方 API 封装，使用 comfy-cli 进行生命周期管理，REST/WebSocket API 执行工作流。

**核心功能**：
- 硬件检测和环境配置
- ComfyUI 安装和启动
- 工作流执行和监控
- 节点和模型管理

**环境变量**：`COMFYUI_HOST`（必需）

#### [`danbooru-tag-scraper/`](modules/danbooru-tag-scraper/SKILL.md)
Danbooru 精细化标签爬取工具，通过代理访问 Danbooru API，按类别批量爬取标签，构建 AI 绘图 prompt 标签词典。

**核心功能**：
- 按类别（发色/瞳色/服装/表情/姿势/背景…）批量爬取标签
- 关联标签发现 · 帖子标签提取
- 角色标签三步法（定系列→提角色→补 wiki）
- 标签分类与去噪

**环境变量**：`HTTPS_PROXY` 或 `ALL_PROXY`（必需，Danbooru 需通过代理访问）

#### [`Tanger-Presets-Show/`](modules/Tanger-Presets-Show/README.md)
Pretags 数据的 Web 可视化管理界面，支持卡片浏览、搜索、编辑、预览图管理。是 pretags.json 的日常管理入口。

**核心功能**：
- 卡片 ID 系统（支持同名卡片）
- 分类浏览和搜索
- 在线编辑和预览
- 预览图上传和管理

**启动方式**：
```bash
cd modules/Tanger-Presets-Show && python3 server.py
# 访问 http://localhost:8765
```

#### [`pretags-draw/`](modules/pretags-draw/SKILL.md)
**主绘图工作流**，整合 tag_producer 中文引擎、ComfyUI 生图、Discord 发图的完整流程。是最终产出图片的核心模块。

**核心工作流**（4 步）：
1. Agent 构建初始提示词
2. tag_producer 处理预设（人物/画风/动作/场景）
3. Agent 翻译 + 增强 + 12 项自检
4. ComfyUI 生图 + 发送

**关键特性**：
- 中文关键词自动转换
- LoRA 格式自动处理
- 画质前缀自动注入
- 多图批量生成
- FaceDetailer 面部修复

**环境变量**：`COMFYUI_HOST`（必需）、`COMFYUI_WORKFLOW_PATH`（可选）、`COMFYUI_OUTPUT_DIR`（可选）
**数据依赖**：`modules/Tanger-Presets-Show/data/pretags.json`（主数据文件）

### 🛠️ 辅助工具模块（`tools/`）

这些工具模块依赖主要功能模块，提供批量操作、测试验证、环境管理等辅助能力。

#### [`artstyle-test/`](tools/artstyle-test/SKILL.md)
画风 LoRA 测试工具，批量生成测试图片验证画风效果。

**依赖**：`pretags-draw` 工作流、`pretags.json` 数据

#### [`pretags-batch-import/`](tools/pretags-batch-import/SKILL.md)
Pretags 数据批量导入和修复工具。

**核心功能**：Excel 批量导入、LoRA 信息修复、数据规范化、画风条目补充入库

**依赖**：`modules/Tanger-Presets-Show/data/pretags.json`、`civitai-api`

#### [`comfyui-startup/`](tools/comfyui-startup/SKILL.md)
ComfyUI 启动脚本和环境管理。

**依赖**：`COMFYUI_HOST` 环境变量

## 🏗️ 工作流架构

### 支持的三种工作流类型

`comfyui_client.py` 通过 `_detect_workflow_type()` 自动识别，根据文件名分发到对应构建方法：

| 类型 | 文件名包含 | 构建方法 | 模型架构 |
|------|-----------|---------|---------|
| **Noob**（默认） | `noob_*` | 原 `_build_workflow` 逻辑 | SDXL（CheckpointLoader + CR Switch） |
| **Anima** | `anima_*` | `_build_workflow_anima()` | Flux（UNETLoader + Qwen CLIP/VAE） |
| **z-image** | `z_image_*` 或 `zturbo` | `_build_workflow_zimage()` | Flux（UNETLoader + Qwen 4B CLIP） |

### 节点ID映射

| 参数 | Noob (node ID) | Anima (node ID) | z-image (node ID) |
|------|---------------|-----------------|-------------------|
| Prompt | 85 | 10 | 31 |
| Negative | 14 | 37 | 7 |
| Width | 20 | 2 | 13(hardcoded) |
| Height | 21 | 3 | 13(hardcoded) |
| KSampler | 48 | 30 | 3 |
| Seed | 32 | 4 | 51 |
| Upscale nodes | 94-97 | 55-62 | 45-50 |

### Hires.fix 放大架构

每种工作流的放大节点结构：

```
Noob:   KSampler[48] → UltimateSDUpscale[94] + UpscaleModelLoader[95] → FaceDetailer[110] → Save[96]/Preview[97]
Anima:  KSamplerAdv[30] → LatentUpscaleBy[55] → KSampler[60] → VAEDecode[56] → FaceDetailer[59] → Preview[58]/Save[62]
z-image: KSampler[3] → LatentUpscaleBy[47] → KSampler[45] → VAEDecode[46] → FaceDetailer[48] → Preview[49]/Save[50]
```

**放大默认不开启**（`upscale=False`）。不开放大时自动移除放大节点。

### ⚠️ 已知陷坑

- **FaceDetailer bbox_detector 缺失**：放大路径的 FaceDetailer 必须连接到 UltralyticsDetectorProvider，否则整条放大分支静默失败。
- **Anima 不开放大时无 FaceDetailer .png**：Anima 工作流在 `upscale=False`（默认）时，移除放大路径节点（67,69,71,72,73,75,76），此时只有 `_0.png`（KSampler 原始输出）+ `_1.epng`（加密保存），**没有 FaceDetailer 修复后的 `_1.png`**。发图时只能发 `_0.png`。
- **Noob vs Anima 模型架构不同**：Noob 用 CheckpointLoader，Anima 用 UNETLoader，不能混用工作流文件。
- **z-image 尺寸硬编码**：`EmptySD3LatentImage[13]` 的宽高是硬编码值，不来自 PrimitiveInt 节点。
- **Anima 工作流专用 JSON**：Anima 工作流使用技能根目录的 `anima-new-Latent.json`。调用时设 `COMFYUI_WORKFLOW_PATH=./anima-new-Latent.json` 并从 skill 根目录运行。
- **Python 环境**：需要 `aiohttp` 包。推荐使用 conda 环境 `comfy311` 运行：`conda run -n comfy311 python3 modules/pretags-draw/scripts/comfyui_draw.py "..." --host ...`
- **输出目录**：所有图片输出到技能根目录的 `output/`。发图前确认文件在 `$SKILL_DIR/output/` 下。

## 🚀 快速开始

### 1. 环境配置

复制 `.env.example` 为 `.env` 并配置必需变量：

```bash
# ComfyUI 服务地址（必需）
COMFYUI_HOST=http://127.0.0.1:8892

# Civitai API 密钥（可选，下载模型需要）
CIVITAI_API_KEY=your_api_key_here

# 工作流模板路径（可选）
COMFYUI_WORKFLOW_PATH=./modules/pretags-draw/assets/noob_api_fix_upscale_face_detailer.json
```

### 2. 安装依赖

```bash
pip install aiohttp pandas numpy openpyxl python-dotenv
```

### 3. 启动 Web 管理界面

```bash
cd modules/Tanger-Presets-Show && python3 server.py &
# 访问 http://localhost:8765
```

### 4. 生成图片

所有图片输出到技能根目录的 `output/` 目录。三种工作流类型通过文件名自动检测：

```bash
cd $SKILL_DIR

# Noob 工作流（文件名为 noob_* 或默认）
python3 modules/pretags-draw/scripts/comfyui_draw.py \
  "masterpiece, best quality, 1girl, white hair, fox ears" \
  --host http://127.0.0.1:8892 --canvas 竖图 --steps 28

# Anima 工作流（文件名含 anima_*，需指定专用 JSON 和 conda 环境）
conda run -n comfy311 python3 modules/pretags-draw/scripts/comfyui_draw.py \
  "1girl, long_hair, grey_hair, ... @ebifurya @tony_taka @ojipon" \
  --host http://127.0.0.1:8892 --canvas 竖图 --steps 20 --cfg 5
```

> **注意**：Anima 工作流需要 `aiohttp` 包，推荐使用 conda 环境 `comfy311`。Anima 工作流必须从 skill 根目录运行并指定 `COMFYUI_WORKFLOW_PATH=./anima-new-Latent.json`。

## 📊 数据结构

### Pretags数据文件

**主文件**：`modules/Tanger-Presets-Show/data/pretags.json`

**结构**（2026-05-20变更为ID-key格式）：
```json
{
  "characters": {
    "c23fe569": {
      "id": "c23fe569",
      "cname": "弗洛洛",
      "source": "鸣潮",
      "name": "frolo",
      "appearance": "1girl, blue eyes, ...",
      "clothing": "dress, ...",
      "has_lora": true,
      "lora_file": "弗洛洛-Frolo",
      "tags": ["1girl", "blue eyes", ...],
      "tags_count": 15
    }
  },
  "categories": {
    "画风": {
      "abc12345": {
        "id": "abc12345",
        "name": "2d润彩",
        "tag": "...",
        "has_lora": true,
        "lora_file": "jijia-gnoobv-000014"
      }
    }
  },
  "series": {
    "鸣潮": {
      "name": "鸣潮",
      "count": 42,
      "characters": ["c23fe569", ...]
    }
  }
}
```

**关键变更**：
- 2026-05-20：从name-key迁移到id-key
- ID生成：MD5(cname+name+source)[:8]
- 支持同名卡片

## 🔧 环境变量说明

### 必需变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `COMFYUI_HOST` | ComfyUI服务地址 | `http://127.0.0.1:8892` |

### 可选变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CIVITAI_API_KEY` | Civitai API密钥 | 无 |
| `COMFYUI_WORKFLOW_PATH` | 工作流模板路径 | `assets/noob_api_fix_upscale_face_detailer.json` |
| `COMFYUI_OUTPUT_DIR` | 输出目录 | `output` |

## 📚 详细文档

### 工作流文档
- [绘图工作流详解](modules/pretags-draw/SKILL.md)
- [Anima Prompt 与工作流指南](references/anima-prompt-and-workflow.md) — 合并: Prompt编写规范、艺术风格切换、骨架映射法、动作技法、工作流使用、放大功能
- [z-image Turbo 工作流指南](references/z-image-guide.md) — 合并: 首次配置、生图参数、LoRA目录(50个)、已验证参数配置(V5 Risograph等)
- [画风管理与测试](references/artstyle-curation.md) — 合并: LoRA整理流程、测试工作流、描述规范(26个已测)、非标准描述检测清理
- [角色预览图生成](references/character-preview-generation.md) — 合并: 批量生成脚本、单角色手动生成、常见陷阱、手动替换预览图

### API文档
- [ComfyUI API参考](modules/comfyui-api/SKILL.md)
- [Civitai API参考](modules/civitai-api/SKILL.md)

### 数据管理
- [Pretags 管理原则](modules/pretags-draw/SKILL.md)
- [Pretags Excel 导入导出](references/pretags-excel-workflow.md) — 合并: 格式版本检测、导出/导入流程、批量操作、常见陷阱
- [Pretags 数据管理](references/pretags-data-management.md) — 合并: 父条目检测清理、LoRA下载注册、批量迁移、双路径同步
- [批量导入工作流](tools/pretags-batch-import/SKILL.md)

### 故障排除
- [ComfyUI 常见陷阱](references/comfyui-pitfalls.md) — 合并: Host URL配置、浏览器API备用方案、history轮询注意事项
- [Docker Sandbox 配置](references/docker-sandbox-guide.md) — 合并: sandbox权限配置、输出路径pitfall、Discord发图路径规则
- [FaceDetailer 管线](references/face-detailer-pipeline.md) — 节点结构、输出文件规则、放大路径必须连接UltralyticsDetectorProvider

### 参考文档
- [环境配置](references/environment-setup.md) — 环境变量、LoRA路径、pretags.json结构
- [Safetensors Tag 提取](references/safetensors-tag-recovery.md) — 元数据tag提取清理、按模型类型策略、批量补全工作流

## ⚠️ 使用规范

### 数据安全
1. **备份优先**：修改 pretags.json 前必须备份
2. **CLI 优先**：数据修改走 CLI，不走 Web API（避免字段丢失）
3. **Server 重启**：修改数据后必须重启 Tanger-Presets-Show 服务

### 路径规范
1. 所有脚本使用相对于技能根目录的相对路径
2. 图片输出统一到技能根目录的 `output/` 目录
3. 软链接：`modules/pretags-draw/assets/pretags.json` → `../../Tanger-Presets-Show/data/pretags.json`

### LoRA 格式
```bash
# ✅ 正确（FEEncLoraAutoLoader）
<lora:露帕-Lupa:0.8:0.8>

# ❌ 错误
<lora:露帕-Lupa.safetensors:0.8:0.8>   # 不要 .safetensors 后缀
<lora:人物/露帕-Lupa:0.8:0.8>          # 不要目录前缀
<露帕-Lupa:0.8:0.8>                    # 缺 lora: 前缀
```

### Anima 画师串格式
Anima 工作流中的画师串使用 `@` 前缀标签格式，放在 prompt 末尾：
```bash
# ✅ 正确
@ebifurya @tony_taka @ojipon
@kawanocy @mignon @hisasi @ask

# ❌ 错误
ebifurya, tony_taka, ojipon             # 缺 @ 前缀
artist:ebifurya                          # 格式不对
```

### 输出文件说明

所有图片输出到技能根目录的 `output/` 目录：

| 工作流 | 文件名 | 说明 |
|--------|--------|------|
| Noob | `_0.png` | KSampler 原始输出 |
| Noob | `_1.png` | FaceDetailer 修复后（推荐用于发图） |
| Noob | `_2.epng` | 加密格式（忽略） |
| Anima（不开放大） | `_0.png` | KSampler 原始输出（无 FaceDetailer） |
| Anima（不开放大） | `_1.epng` | 加密格式（忽略） |
| Anima（开放大） | `_1.png` | FaceDetailer 修复后 |

## 🔄 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-05-21 | Tanger-Presets-Show ID 系统重构，数据迁移至 id-key 格式 |
| v1.1.0 | 2026-05-27 | 新增工作流类型自动检测（Noob/Anima/z-image），Hires.fix 放大管线 |
| v1.2.0 | 2026-05-28 | Anima 放大管线升级，FaceDetailer bbox_detector 修复 |
| v1.3.0 | 2026-06-01 | 画师串 @ 前缀规范，Anima 专用工作流 JSON，输出路径标准化 |
| v1.3.1 | 2026-06-02 | references/ 文档精简合并（43→11），模块结构标准化（modules/tools） |

## 📄 许可证

MIT License