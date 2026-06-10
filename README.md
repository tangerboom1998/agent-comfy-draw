# ComfyUI Draw

基于 ComfyUI 的 AI 绘图工具集，包含角色管理、标签系统、画风测试、批量导入等工作流。

> **设计定位**：本工具主要为 AI Agent 使用，帮助 Agent 更好地生成提示词和调用工作流，整体偏向二次元角色处理。大部分代码由 AI 生成。

## 📦 前置依赖

项目中的 ComfyUI 工作流需要以下自定义节点：

- **[fexli-util-node-comfyui](custom_nodes/fexli-util-node-comfyui/)** — 内置，已包含在仓库中
- **[ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack)** — 需手动克隆到 ComfyUI 的 `custom_nodes/` 目录：
  ```bash
  cd /path/to/ComfyUI/custom_nodes
  git clone https://github.com/ltdrdata/ComfyUI-Impact-Pack.git
  ```

## 🚀 快速开始

### 环境配置

```bash
pip install -r requirements.txt
```

**注意**：本项目主要为 AI Agent 使用，环境变量需设置在 Agent 的运行环境（如 `~/.bashrc` 或 Agent 配置的 `.env`）中，在项目目录下编辑 `.env` 文件不会生效。详见 [`.env.example`](.env.example)。

### 启动管理界面
```bash
cd modules/Tanger-Presets-Show && python server.py
# 访问 http://localhost:8765
```

### 可选：下载角色预览图 (675MB)

该数据集包含大量角色的预览图，用于 Tanger-Presets-Show 管理界面展示。

```bash
pip install modelscope
cd modules/Tanger-Presets-Show/data
modelscope download --dataset tangerboom/character-data character-data.tar.gz --local_dir ./
tar xzf character-data.tar.gz && rm character-data.tar.gz
cd ../../..
# 数据来源：https://github.com/hbl917070/DrawingSpells
```

## ⚙️ 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `COMFYUI_HOST` | ComfyUI 服务地址 `http://127.0.0.1:8188` | ✅ |
| `COMFYUI_PATH` | ComfyUI 安装路径 | |
| `CONDA_PATH` / `CONDA_ENV` | Conda 路径和环境名 | |
| `CUDA_VISIBLE_DEVICES` | GPU 配置（如 `0` 或 `1,0`） | |
| `CIVITAI_API_KEY` / `CIVITAI_HOST` | Civitai API 密钥和地址 | |
| `WEB_SHOW_PORT` | Web 服务端口（默认 `8765`） | |
| `LORA_MODEL_DIR` | LoRA 模型目录 | |
| `HTTP_PROXY` / `HTTPS_PROXY` | 代理地址 | |

完整示例见 [`.env.example`](.env.example)。

## 📂 项目结构

```
comfyui-draw/
├── custom_nodes/                # ComfyUI 自定义节点
│   └── fexli-util-node-comfyui/ # 内置节点
├── pretags/                     # 角色标签数据 (19,000+ 角色)
├── modules/
│   ├── comfyui-api/             # ComfyUI API 封装（独立模块）
│   ├── Tanger-Presets-Show/     # 角色标签管理系统（独立模块）
│   ├── civitai-api/             # Civitai 模型管理（独立模块）
│   └── pretags-draw/            # 核心绘图工作流
├── tools/
│   ├── pretags-batch-import/    # 批量导入工具
│   ├── artstyle-test/           # 画风测试工具
│   └── comfyui-startup/         # ComfyUI 启动管理
├── references/                  # 参考文档
├── output/                      # 生成图片输出
├── .env.example
└── requirements.txt
```

## 📚 模块说明

| 模块 | 说明 | 文档 |
|------|------|------|
| **comfyui-api** | ComfyUI REST API 和 WebSocket 封装 | [`modules/comfyui-api/SKILL.md`](modules/comfyui-api/SKILL.md) |
| **Tanger-Presets-Show** | 角色标签管理系统（Web UI + API） | [`SKILL.md`](SKILL.md) |
| **civitai-api** | Civitai 模型搜索、下载、哈希查询 | [`modules/civitai-api/SKILL.md`](modules/civitai-api/SKILL.md) |
| **pretags-draw** | 核心绘图工作流（4 步流程） | [`modules/pretags-draw/SKILL.md`](modules/pretags-draw/SKILL.md) |
| **pretags-batch-import** | 批量导入角色和标签 | [`tools/pretags-batch-import/SKILL.md`](tools/pretags-batch-import/SKILL.md) |
| **artstyle-test** | 画风 LoRA 批量测试 | [`tools/artstyle-test/SKILL.md`](tools/artstyle-test/SKILL.md) |
| **comfyui-startup** | ComfyUI 启动和健康检查 | [`tools/comfyui-startup/SKILL.md`](tools/comfyui-startup/SKILL.md) |

## 📖 文档索引

- 项目总览：[`SKILL.md`](SKILL.md)
- 参考文档：[`references/`](references/) 目录下含 Anima Prompt、画风管理、预览图生成、环境配置、工作流节点映射等详细说明

## 📄 许可证

MIT License — 详见 [LICENSE](LICENSE)。
