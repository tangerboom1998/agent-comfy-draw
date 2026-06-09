# ComfyUI Draw 项目套件

一个基于 ComfyUI 的 AI 绘图工具集，包含角色管理、标签系统、画风测试、批量导入等完整工作流。

## 🎯 核心特性

- **角色标签管理**：19,000+ 角色和 10,000+ 标签的 Web 管理系统
- **智能绘图工作流**：4 步流程，从角色选择到图片生成
- **模型管理**：Civitai 模型搜索、下载、自动放置
- **批量操作**：批量导入、预览图生成、画风测试
- **环境变量配置**：所有路径和配置通过 `.env` 文件管理
- **跨平台支持**：使用相对路径，支持 Windows/Linux/macOS

## ⚙️ 环境变量配置

### 必需配置

在使用项目前，必须配置以下环境变量：

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，配置必需项
nano .env  # 或使用其他编辑器
```

**必需的环境变量：**

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `COMFYUI_HOST` | ComfyUI 服务地址 | `http://127.0.0.1:8188` |

### 可选配置

根据使用的模块，可能需要配置以下环境变量：

#### ComfyUI 本地启动（comfyui-startup 模块）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `COMFYUI_PATH` | ComfyUI 安装路径 | `/path/to/ComfyUI` |
| `CONDA_PATH` | Conda 安装路径 | `/path/to/anaconda3` |
| `CONDA_ENV` | Conda 环境名 | `comfy311` |
| `CUDA_VISIBLE_DEVICES` | GPU 配置 | `0` 或 `1,0` |

#### Civitai API（civitai-api 模块）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `CIVITAI_API_KEY` | Civitai API 密钥 | `your_api_key_here` |
| `CIVITAI_HOST` | Civitai API 地址 | `https://civitai.com` |

#### Tanger-Presets-Show 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `WEB_SHOW_PORT` | Web 服务端口 | `8765` |

#### LoRA 模型路径

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `LORA_MODEL_DIR` | LoRA 模型根目录 | `/path/to/ComfyUI/models/loras` |

#### 代理配置（可选）

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `HTTP_PROXY` | HTTP 代理地址 | `http://proxy.example.com:2090` |
| `HTTPS_PROXY` | HTTPS 代理地址 | `http://proxy.example.com:2090` |

### 完整配置示例

```bash
# ComfyUI 服务地址（必需）
COMFYUI_HOST=http://127.0.0.1:8188

# ComfyUI 本地启动配置（可选）
COMFYUI_PATH=/home/user/ComfyUI
CONDA_PATH=/home/user/anaconda3
CONDA_ENV=comfy311
CUDA_VISIBLE_DEVICES=0

# Civitai API（可选）
CIVITAI_API_KEY=your_api_key_here

# Tanger-Presets-Show 配置
WEB_SHOW_PORT=8765

# LoRA 模型路径（可选）
LORA_MODEL_DIR=/home/user/ComfyUI/models/loras
```

## 📦 项目结构

```
comfyui-draw/
├── LICENSE                     # MIT 许可证
├── requirements.txt            # Python 依赖列表
├── SKILL.md                    # 项目总览和快速开始指南
├── .env.example                # 环境变量配置模板
├── README.md                   # 本文件
│
├── pretags/                    # 角色标签数据文件（主存储位置）
│   ├── pretags-anima.json      # Anima 工作流数据（19MB，19,000+ 角色）
│   └── pretags-ill-noob.json   # Illustrious/Noob 工作流数据（20MB）
│
├── modules/comfyui-api/                # ComfyUI API 封装（独立模块）
│   ├── SKILL.md                # ComfyUI API 使用文档
│   └── workflows/              # 预设工作流
│
├── modules/Tanger-Presets-Show/              # 角色标签管理系统（独立模块）
│   ├── server.py               # Web 服务器（智能路径解析）
│   ├── index.html              # Web 管理界面
│   ├── data/                   # 数据目录（符号链接到 ../../pretags/）
│   └── imgs/                   # 预览图资源（724MB）
│
├── modules/civitai-api/                # Civitai API 封装（独立模块）
│   ├── SKILL.md                # Civitai API 使用文档
│   └── scripts/civitai.py      # API 客户端
│
├── modules/pretags-draw/               # 核心绘图工作流（依赖模块）
│   ├── SKILL.md                # 绘图工作流文档
│   ├── scripts/                # 绘图脚本
│   └── assets/                 # 工作流资源
│
├── tools/                      # 辅助工具
│   ├── pretags-batch-import/   # 批量导入工具
│   ├── artstyle-test/          # 画风测试工具
│   └── comfyui-startup/        # ComfyUI 启动管理
│
├── output/                     # 生成图片输出目录
└── references/                 # 项目参考文档（简洁精炼）
    ├── anima-prompt-and-workflow.md    # Anima Prompt 与工作流指南
    ├── artstyle-curation.md            # 画风管理与测试
    ├── character-preview-generation.md # 角色预览图生成
    ├── comfyui-pitfalls.md             # ComfyUI 常见陷阱
    ├── environment-setup.md            # 环境配置
    ├── pretags-data-management.md      # Pretags 数据管理
    ├── pretags-draw-rules.md           # Pretags Draw 使用规则
    ├── pretags-excel-workflow.md       # Pretags Excel 导入导出
    ├── safetensors-tag-recovery.md     # Safetensors Tag 提取
    ├── workflow-node-mapping.md        # 工作流节点映射
    └── z-image-guide.md                # z-image Turbo 工作流
```

## 🚀 快速开始

### 1. 环境准备

**必需依赖：**
- Python 3.8+
- ComfyUI（本地或远程部署）

**可选依赖：**
- Civitai API Key（用于模型下载）

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必需项：
# COMFYUI_HOST=http://127.0.0.1:8188
# PRETAGS_DATA_PATH=./pretags/pretags-anima.json
```

### 3. 准备 Pretags 数据

```bash
# 复制示例数据文件（首次使用）
cd pretags/
cp example-pretags-anima.json pretags-anima.json
# 或使用 Illustrious/Noob 工作流：
# cp example-pretags-ill-noob.json pretags-ill-noob.json

# 详见 pretags/README.md
```

### 4. 安装 Python 依赖

```bash
# 推荐使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install websocket-client requests python-dotenv pillow
```

### 5. 下载角色预览图数据（可选）
```bash
# 角色预览图数据 (675MB) 来自 DrawingSpells 数据集
# 安装 ModelScope 并下载到 data 目录后解压
pip install modelscope
cd modules/Tanger-Presets-Show/data
modelscope download --dataset tangerboom/character-data character-data.tar.gz --local_dir ./
tar xzf character-data.tar.gz    # 解压出 character/ 目录
rm character-data.tar.gz          # 可选：删除压缩包节省空间
cd ../../..

# 数据来源：https://github.com/hbl917070/DrawingSpells (已获授权使用)
```

解压后目录结构：
```
modules/Tanger-Presets-Show/data/
├── characterList.js           # 角色索引（已有）
├── imageCountList.js          # 图片统计（已有）
├── character-previews/        # 手动设置的预览图
└── character/                 # 14,000+ 张角色预览图
    ├── 00094-3137981235.webp
    └── ...
```

### 6. 启动 Tanger-Presets-Show 管理界面

```bash
cd Tanger-Presets-Show
python server.py

# 访问 http://localhost:8765
```

### 7. 开始绘图

参考 [`pretags-draw/SKILL.md`](modules/pretags-draw/SKILL.md) 了解完整的绘图工作流。

**快速示例：**

```bash
cd modules/pretags-draw/scripts

# 使用 tag_producer 生成提示词
python tag_producer.py --preset 角色名称

# 执行绘图
python comfyui_draw.py --prompt "your prompt here"
```

## 📚 模块说明

### 独立模块（可单独使用）

| 模块 | 说明 | 文档 |
|------|------|------|
| **comfyui-api** | ComfyUI REST API 和 WebSocket 封装 | [`comfyui-api/SKILL.md`](modules/comfyui-api/SKILL.md) |
| **Tanger-Presets-Show** | 角色标签管理系统（Web UI + API） | 见根目录 [`SKILL.md`](SKILL.md) |
| **civitai-api** | Civitai 模型搜索、下载、哈希查询 | [`civitai-api/SKILL.md`](modules/civitai-api/SKILL.md) |

### 依赖模块（需要独立模块支持）

| 模块 | 说明 | 依赖 | 文档 |
|------|------|------|------|
| **pretags-draw** | 核心绘图工作流（4步流程） | comfyui-api, Tanger-Presets-Show | [`pretags-draw/SKILL.md`](modules/pretags-draw/SKILL.md) |
| **pretags-batch-import** | 批量导入角色和标签 | Tanger-Presets-Show, civitai-api | [`pretags-batch-import/SKILL.md`](tools/pretags-batch-import/SKILL.md) |
| **artstyle-test** | 画风 LoRA 批量测试 | comfyui-api, Tanger-Presets-Show | [`artstyle-test/SKILL.md`](tools/artstyle-test/SKILL.md) |
| **comfyui-startup** | ComfyUI 启动和健康检查 | comfyui-api | [`comfyui-startup/SKILL.md`](tools/comfyui-startup/SKILL.md) |

## 🎯 核心功能

### 1. 角色标签管理（Tanger-Presets-Show）

- **Web 管理界面**：可视化管理 19,000+ 角色和 10,000+ 标签
- **ID-key 架构**：基于 MD5 的稳定 ID 系统（8字符）
- **智能路径解析**：自动搜索 `pretags/` 目录或使用 `PRETAGS_DATA_PATH` 环境变量
- **多数据文件支持**：支持多个 pretags.json 文件（如 anima、ill-noob）
- **LoRA 集成**：角色关联 LoRA 模型和触发词
- **预览图管理**：角色和标签预览图自动关联
- **实时搜索**：按名称、来源、系列、标签搜索

**数据文件位置**：
- 主存储：`pretags/pretags-anima.json`、`pretags/pretags-ill-noob.json`
- 符号链接：`modules/Tanger-Presets-Show/data/` → `../../pretags/`
- 自定义路径：通过 `PRETAGS_DATA_PATH` 环境变量指定

### 2. 绘图工作流（pretags-draw）

**4 步核心流程：**

1. **构建初始提示词**：从 pretags 数据提取角色信息
2. **tag_producer 预设处理**：应用预设模板和 LoRA
3. **Agent 翻译增强**：中文转英文 + 提示词优化
4. **生图发送**：调用 ComfyUI 生成并返回结果

### 3. 模型管理（civitai-api）

- 搜索和下载 Civitai 模型
- 哈希查询和验证
- 自动放置到 ComfyUI 目录
- Vault 管理（需要会员）

### 4. 批量操作

- **批量导入**：从 Excel 导入角色数据
- **批量生成预览图**：为角色批量生成预览图
- **画风测试**：批量测试画风 LoRA 效果

## 📐 路径规范

项目使用**相对路径**，确保跨平台兼容性：

```python
# ✅ 正确：使用相对路径
import os
from pathlib import Path

# 方式 1：相对于当前脚本路径
script_dir = Path(__file__).resolve().parent
pretags_path = script_dir.parent / "pretags" / "pretags-anima.json"

# 方式 2：使用环境变量（推荐）
pretags_path = os.getenv("PRETAGS_DATA_PATH", "./pretags/pretags-anima.json")

# ❌ 错误：硬编码绝对路径
pretags_path = "/home/user/comfyui-draw/pretags/pretags-anima.json"
```

## 🔧 开发指南

### 数据结构

**Pretags 数据格式（ID-key 结构，自 2026-05-20）：**

**数据文件位置**：
- `pretags/pretags-anima.json` - Anima 工作流数据（19MB）
- `pretags/pretags-ill-noob.json` - Illustrious/Noob 工作流数据（20MB）

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
    "e5f6g7h8": {
      "id": "e5f6g7h8",
      "name": "标签名",
      "category": "类别",
      "tags": "tag1, tag2",
      "desc": "描述",
      "dgroup": "分组"
    }
  },
  "series": {
    "系列名": {
      "source": "来源",
      "characters": ["a1b2c3d4", ...]
    }
  }
}
```

### ID 生成规则

```python
import hashlib

def generate_card_id(card_type, **fields):
    """
    生成稳定的 8 字符 ID
    - characters: MD5(cname + name + source)
    - categories: MD5(name + category)
    """
    if card_type == "character":
        key = f"{fields['cname']}_{fields['name']}_{fields['source']}"
    elif card_type == "category":
        key = f"{fields['name']}_{fields['category']}"
    return hashlib.md5(key.encode('utf-8')).hexdigest()[:8]
```

### 添加新功能

1. 在对应模块目录创建脚本
2. 更新模块的 `SKILL.md` 文档
3. 如需环境变量，更新 `.env.example`
4. 提交前运行测试

## 📖 文档索引

- **项目总览**：[`SKILL.md`](SKILL.md)
- **ComfyUI API**：[`comfyui-api/SKILL.md`](modules/comfyui-api/SKILL.md)
- **Civitai API**：[`civitai-api/SKILL.md`](modules/civitai-api/SKILL.md)
- **绘图工作流**：[`pretags-draw/SKILL.md`](modules/pretags-draw/SKILL.md)
- **批量导入**：[`pretags-batch-import/SKILL.md`](tools/pretags-batch-import/SKILL.md)
- **画风测试**：[`artstyle-test/SKILL.md`](tools/artstyle-test/SKILL.md)
- **启动管理**：[`comfyui-startup/SKILL.md`](tools/comfyui-startup/SKILL.md)

### Reference 文档
- [Anima Prompt 与工作流](references/anima-prompt-and-workflow.md)
- [画风管理与测试](references/artstyle-curation.md)
- [角色预览图生成](references/character-preview-generation.md)
- [ComfyUI 常见陷阱](references/comfyui-pitfalls.md)
- [环境配置](references/environment-setup.md)
- [Pretags 数据管理](references/pretags-data-management.md)
- [Pretags Draw 使用规则](references/pretags-draw-rules.md)
- [Pretags Excel 导入导出](references/pretags-excel-workflow.md)
- [Safetensors Tag 提取](references/safetensors-tag-recovery.md)
- [工作流节点映射](references/workflow-node-mapping.md)
- [z-image Turbo 工作流](references/z-image-guide.md)
- [项目警告汇总](WARNINGS.md)

## ⚠️ 常见问题

### 1. 数据文件找不到

Tanger-Presets-Show 使用智能路径解析，按以下顺序查找数据文件：

```bash
# 1. 检查环境变量（优先级最高）
echo $PRETAGS_DATA_PATH

# 2. 检查 pretags/ 目录
ls -lh pretags/*.json

# 3. 检查符号链接
ls -lh modules/Tanger-Presets-Show/data/*.json

# 自定义数据文件位置（推荐）
export PRETAGS_DATA_PATH=/path/to/your/pretags-anima.json
# 或在 .env 文件中设置
echo "PRETAGS_DATA_PATH=./pretags/pretags-anima.json" >> .env
```

### 2. ComfyUI 连接失败

```bash
# 检查 ComfyUI 是否运行
curl http://127.0.0.1:8188/system_stats

# 检查 .env 配置
cat .env | grep COMFYUI_HOST
```

### 3. LoRA 路径错误

确保 LoRA 格式包含 `lora:` 前缀：

```python
# ✅ 正确
lora_str = "lora:character_name:0.8"

# ❌ 错误
lora_str = "character_name:0.8"
```

### 4. 预览图不显示

检查预览图路径和文件是否存在：

```bash
ls -la Tanger-Presets-Show/imgs/characters/
ls -la Tanger-Presets-Show/imgs/tags/
```

### 5. 数据迁移问题

如需回滚到旧的 name-key 结构：

```bash
cd Tanger-Presets-Show
python rollback_to_name_key.py
```

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 📦 角色预览图数据集

角色预览图数据 (`character-data.tar.gz`, 675MB) 来源于 [DrawingSpells](https://github.com/hbl917070/DrawingSpells) 项目，已获授权在本项目中使用。

**下载方式**：
```bash
pip install modelscope
cd modules/Tanger-Presets-Show/data/
modelscope download --dataset tangerboom/character-data character-data.tar.gz --local_dir ./
tar xzf character-data.tar.gz
rm character-data.tar.gz
cd ../../..
```

该数据集包含 19,000+ 角色的预览图，用于 Tanger-Presets-Show 管理界面展示。

## 🙏 致谢

- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 强大的 AI 图像生成框架
- [Civitai](https://civitai.com) - 模型分享社区
- [DrawingSpells](https://github.com/hbl917070/DrawingSpells) - 角色预览图数据集
- 所有贡献者和用户

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发起 Discussion
- 邮件联系（如有）

---

**最后更新**：2026-05-22
**版本**：2.0.0（ID-key 架构）
