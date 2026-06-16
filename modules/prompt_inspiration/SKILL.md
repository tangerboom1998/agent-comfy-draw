---
name: prompt-inspiration
description: "图像打标数据灵感检索 + 图片自动打标工具：基于 2738 份打标数据，支持语义搜索、标签精确过滤、VLM/WD 自动打标。"
version: 0.1.0
metadata:
  openclaw:
    emoji: "💡"
    requires:
      env: ["HTTPS_PROXY"]
---

# Prompt Inspiration Tool

图像打标数据灵感检索 + 图片自动打标工具。基于 2738 份打标数据，支持语义搜索、标签精确过滤、图片自动生成打标。

## 环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `HTTPS_PROXY` | 代理地址（模型下载/VLM 调用需要） | ✅ |
| `VLM_API_BASE` | VLM API 地址（默认 `https://token-plan-cn.xiaomimimo.com/v1`） | |
| `VLM_API_KEY` | VLM API 密钥 | 调用 VLM 时必需 |
| `VLM_MODEL` | VLM 模型名（默认 `mimo-v2.5`） | |

## 下载数据

```bash
pip install modelscope
cd modules/prompt_inspiration

# 1. 下载打标数据（2738 份提示词，1MB）
modelscope download --dataset tangerboom/character-data prompts.tar.gz --local_dir ./
tar xzf prompts.tar.gz && rm prompts.tar.gz

# 2. 下载 WD Tagger 模型（388MB，可选 — 仅图片打标需要）
modelscope download --dataset tangerboom/character-data tagger_models.tar.gz --local_dir ./
mkdir -p models/tagger_models
tar xzf tagger_models.tar.gz -C models/tagger_models && rm tagger_models.tar.gz
```

## 功能

### 搜索灵感 `search`

语义/标签/混合搜索打标库。三种模式：

- `hybrid`（默认）— 语义相似度 + 标签匹配混合排序
- `semantic` — 纯语义向量搜索（ONNX MiniLM-L6-v2 或 TF-IDF 降级）
- `tag` — 仅标签精确匹配（AND 逻辑）

```bash
python3 -m prompt_inspiration.cli search "cyberpunk female warrior" --top-k 5
python3 -m prompt_inspiration.cli search "mecha" --tags mecha solo --mode hybrid
python3 -m prompt_inspiration.cli search "" --tags "1girl" portrait --mode tag --json
```

参数：
| 参数 | 默认 | 说明 |
|------|------|------|
| `query` | 必填 | 自然语言描述 |
| `--tags, -t` | — | 标签过滤（AND，空格分隔） |
| `--top-k, -k` | 10 | 返回条数（最大 50） |
| `--mode, -m` | hybrid | semantic / tag / hybrid |
| `--json, -j` | — | JSON 格式输出 |

### 图片打标 `tag`

对图片自动生成打标。两种引擎：

- **WD Tagger** — 本地 WD14 ONNX 模型（388MB），毫秒级推理，输出 Danbooru 风格标签
- **VLM Tagger** — 调用多模态 API，输出逗号分隔的描述短语

三种模式：
- `tags` — 仅 WD 标签
- `caption` — 仅 VLM 描述
- `both`（默认）— WD 标签在前，VLM 描述在后，合并输出

```bash
python3 -m prompt_inspiration.cli tag photo.png
python3 -m prompt_inspiration.cli tag photo.png --mode tags --threshold 0.4
python3 -m prompt_inspiration.cli tag photo.png --mode caption
python3 -m prompt_inspiration.cli tag photo.png --save --rebuild
```

参数：
| 参数 | 默认 | 说明 |
|------|------|------|
| `images` | 必填 | 图片路径（可多个） |
| `--mode, -m` | both | tags / caption / both |
| `--save, -s` | — | 保存到 prompts/ 库 |
| `--rebuild, -r` | — | 保存后重建搜索索引 |
| `--threshold` | 0.35 | WD 常规标签阈值 |
| `--char-threshold` | 0.85 | WD 角色标签阈值 |
| `--additional-tags` | — | 始终包含的标签 |
| `--exclude-tags` | — | 排除的标签 |
| `--vlm-prompt` | — | 自定义 VLM 提示词 |
| `--max-tokens` | 8192 | VLM 最大 token |

输出格式：**逗号连接，无句号，无句子**（WD 和 VLM 统一格式）。

### 索引管理 `build` / `setup` / `info`

```bash
python3 -m prompt_inspiration.cli build    # 从 prompts/ 重建全部索引
python3 -m prompt_inspiration.cli setup    # 下载 ONNX 模型 + 构建索引
python3 -m prompt_inspiration.cli info     # 查看索引/模型状态
```

## 项目结构

```
prompt_inspiration/
├── SKILL.md                        ← 本文件
├── pyproject.toml                  # Python 包配置
├── prompt_inspiration/
│   ├── cli.py                      CLI 入口
│   ├── searcher.py                 搜索引擎
│   ├── indexer.py                  索引构建
│   ├── model_setup.py              ONNX 模型
│   ├── tool.py                     agent 接口
│   ├── config.py                   路径与配置
│   └── tagger/
│       ├── wd.py                   WD14 标签预测
│       └── vlm.py                  VLM 自然语言打标
├── prompts/                        打标数据
├── data/                           构建后的索引
├── models/                         下载的 ONNX 模型
└── tests/                          测试
```

## 完整工作流

```bash
# 1. 设置代理（如需）
export HTTPS_PROXY=http://127.0.0.1:7890

# 2. 查看状态
prompt-inspiration info

# 3. 搜索灵感
prompt-inspiration search "cyberpunk girl with neon hair" --top-k 5

# 4. 对参考图打标
prompt-inspiration tag ./reference.png --mode both

# 5. 保存到库并重建索引
prompt-inspiration tag ./reference.png --save --rebuild

# 6. 新内容可检索
prompt-inspiration search "刚才那张图" --top-k 3
```
