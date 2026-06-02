# Docker Sandbox + ComfyUI 配置指南

> 合并自: docker-sandbox-comfyui.md, docker-sandbox-output-pitfall.md

---

## 场景

在 Docker sandbox 环境中运行 comfyui_draw.py，需要配置 sandbox 权限和路径映射。

## 配置步骤

### 1. 启用 terminal 工具集

```yaml
# 从 disabled_toolsets 中移除 terminal
disabled_toolsets: []
# 或至少确保 terminal 不在禁用列表中
```

### 2. docker_env 传递 COMFYUI_HOST

```yaml
docker_env:
  COMFYUI_HOST: "http://host.docker.internal:8188"
  LORA_MODEL_DIR: "/workspace/loras"
```

### 3. 挂载 skills 和 output

```yaml
docker_volumes:
  - /path/to/skills:/workspace/skills:ro  # skills 只读
  - /path/to/output:/workspace/output     # output 可写
```

---

## 输出路径 Pitfall

### 问题

在 Docker sandbox 中生成的图片，无法通过 Discord 发送（路径不可访问）。

### 根因

Docker 容器内的路径（如 `/workspace/output/xxx.png`）在宿主机上不存在。Discord 发图需要**宿主机路径**。

### 解决方案

```python
# 从 /tmp 运行（/tmp 在容器内始终可写）
import tempfile, shutil
tmpdir = tempfile.mkdtemp()
# ... 在 tmpdir 中操作

# 复制到 /workspace/output/（容器内共享挂载目录）
shutil.copy(f'{tmpdir}/result.png', '/workspace/output/result.png')
```

### ⚠️ Discord 发图：必须用宿主机路径

```python
# ✅ 正确 — 宿主机路径
MEDIA = "/home/user/output/result.png"

# ❌ 错误 — 容器路径，Discord 无法解析
MEDIA = "/workspace/output/result.png"
```

### 关键路径

| 环境 | 路径 |
|------|------|
| 容器内 | `/workspace/output/` |
| 宿主机（发图用） | `/home/user/output/` |
| ComfyUI output | `~/lr/ComfyUI/output/` |

---

## 依赖问题

Docker 镜像可能缺少 Python 依赖：

```bash
# 常见缺失
pip install aiohttp openpyxl Pillow
```

### 网络连通性验证

```bash
# 从容器内验证 ComfyUI 连通性
curl http://host.docker.internal:8188/system_stats
```

---

## 安全性

- skills 目录挂载为只读（`:ro`）
- output 目录可写但限制大小
- 不要在 Docker 容器中存储敏感信息
