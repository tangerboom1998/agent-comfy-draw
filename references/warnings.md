# ⚠️ 项目警告和注意事项

本文档收集项目中的所有警告、陷阱和注意事项。

---

## 🎨 ComfyUI 相关

### Host URL 配置
- 确保 `COMFYUI_HOST` 使用完整 URL（如 `http://127.0.0.1:8188`）
- 不要使用简写（如 `localhost:8188`）

### 工作流文件
- 生图时必须通过 `--workflow` 参数指定工作流（`anima`/`noob`/`zimage`）
- 由 Agent 根据用户需求选择合适的工作流，不要依赖默认值

### FaceDetailer
- 放大路径的 FaceDetailer 必须连接 UltralyticsDetectorProvider
- 否则整条放大分支会静默失败

---

## 📊 Pretags 数据

### LoRA 兼容性
- **LoRA 文件分模型架构** - SDXL 训练的 LoRA 不能在 Flux 模型上用，反之亦然
- **Noob 工作流**: 使用 SDXL 模型，支持 SDXL LoRA
- 不要在 pretags-anima.json 中添加带 LoRA 的词条

### Name 字段规则
- `name` 字段不可省略，即使角色有 LoRA
- 无 LoRA 时：`name` 是唯一的角色标识
- 有 LoRA 时：`name` 提供辅助信息

### Solo 标签
- 所有单角色绘图必须包含 `solo` 标签
- 不加会导致重影、多人物、边界模糊

---

## 🔧 开发相关

### 路径规范
- 使用相对路径，不要硬编码绝对路径
- 通过环境变量配置路径（`LORA_MODEL_DIR`, `COMFYUI_PATH`）

### Git 操作
- 不要直接推送到 main/master 分支
- 使用新分支进行开发
- PR 标题保持简洁（<70 字符）

### Python 环境
- Anima 工作流需要 `aiohttp` 包
- 推荐使用 conda 环境 `comfy311`

### Docker Sandbox 配置
**如果在 Docker Sandbox 环境中运行**：

- **路径映射**: 
  - 容器内：`/workspace/output/`
  - 宿主机：`/home/user/output/`
  - Discord 发图必须使用宿主机路径

- **环境变量**:
  ```yaml
  docker_env:
    COMFYUI_HOST: "http://host.docker.internal:8188"
  ```

- **依赖**: Docker 镜像可能缺少 `aiohttp`, `openpyxl`, `Pillow`

---

## 🌐 外部 API

### Civitai API
- NSFW 内容需要 API key
- 下载模型需要认证
- API 可能返回 SSL EOF 错误，需重试

### Danbooru API
- **必须使用代理访问**
- 连续请求间隔 ≥ 1 秒
- 单次脚本不超过 100 个请求

---

## 📝 文档编写

### SKILL.md 规范
- 长度控制在 200-400 行
- 警告不超过 3 条
- 不要包含个人化语言、时间戳
- 技术细节归档到 references/

### Reference 规范
- 每个文档 ≤ 150 行
- 只保留核心流程和关键决策点
- 不要包含详细代码实现

---

## 🤖 Agent 行为约束

### 禁止操作（未经用户明确允许）
- ❌ 修改任何 SKILL.md 文档
- ❌ 修改项目代码文件
- ❌ 删除或重命名文件
- ❌ 修改 Git 配置

### 允许操作
- ✅ 根据用户习惯新增 reference 文档（保持简洁）
- ✅ 向 WARNINGS.md 添加新的警告或提醒
- ✅ 创建临时分析报告（`*_REPORT.md`, `*_AUDIT.md`）
- ✅ 回答问题和提供建议

### Reference 创建规范
- 文档必须 ≤ 150 行
- 格式遵循 REFERENCE_TEMPLATE.md
- 内容简洁、准确、有效
- 只包含核心信息，不包含实现细节

---

**最后更新**: 2026-06-07
