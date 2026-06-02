# ComfyUI Draw 项目发布检查清单

## 📋 发布前检查

### 1. 环境配置

- [ ] 复制 `.env.example` 为 `.env`
- [ ] 配置 `COMFYUI_HOST`（必需）
- [ ] 配置 `CIVITAI_API_KEY`（可选）
- [ ] 验证所有路径配置正确

### 2. 依赖安装

```bash
# Python 依赖
pip install websocket-client requests python-dotenv pillow openpyxl

# 验证 Python 版本
python --version  # 需要 3.8+
```

### 3. 数据完整性

- [ ] 验证 `Tanger-Presets-Show/data/pretags.json` 存在
- [ ] 确认数据使用 ID-key 结构（2026-05-20 后）
- [ ] 检查预览图目录：
  - `Tanger-Presets-Show/imgs/characters/`
  - `Tanger-Presets-Show/imgs/tags/`

### 4. 服务启动测试

```bash
# 启动 Tanger-Presets-Show 管理界面
cd Tanger-Presets-Show
python server.py

# 访问 http://localhost:8765
# 验证：
# - 角色列表加载正常
# - 标签列表加载正常
# - 搜索功能正常
# - 编辑功能正常
```

### 5. 核心功能测试

#### Tanger-Presets-Show Web 界面
- [ ] 角色搜索和筛选
- [ ] 标签搜索和筛选
- [ ] 角色编辑（包括预览图重命名）
- [ ] 标签编辑（包括预览图重命名）
- [ ] 新增角色
- [ ] 新增标签
- [ ] 删除功能

#### ComfyUI API
```bash
cd comfyui-api
# 测试连接
curl http://127.0.0.1:8188/system_stats
```

#### Civitai API
```bash
cd modules/civitai-api/scripts
# 测试搜索
python civitai.py search "character name"
```

#### 绘图工作流
```bash
cd modules/pretags-draw/scripts
# 测试 tag_producer
python tag_producer.py --preset 角色名称

# 测试生图（需要 ComfyUI 运行）
python comfyui_draw.py "test prompt"
```

### 6. 文档检查

- [ ] README.md 完整且准确
- [ ] SKILL.md 包含所有模块说明
- [ ] 各模块 SKILL.md 文档完整
- [ ] .env.example 包含所有必需配置
- [ ] 示例命令可执行

### 7. 代码质量

- [ ] 无硬编码的绝对路径
- [ ] 使用相对路径或环境变量
- [ ] 敏感信息不在代码中
- [ ] 备份机制正常工作

### 8. Git 准备

```bash
# 检查 .gitignore
cat .gitignore

# 确认以下文件被忽略：
# - .env
# - __pycache__/
# - *.pyc
# - output/*.png
# - Tanger-Presets-Show/data/*.backup
```

### 9. 安全检查

- [ ] 无 API 密钥在代码中
- [ ] 无个人路径信息
- [ ] 无敏感数据在仓库中
- [ ] .env 文件在 .gitignore 中

### 10. 性能验证

- [ ] Tanger-Presets-Show 加载 19,000+ 角色正常
- [ ] 搜索响应时间 < 1秒
- [ ] 预览图加载正常
- [ ] 大批量操作不崩溃

## 🚀 发布步骤

### 1. 清理临时文件

```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清理输出文件（可选）
# rm -f output/*.png
```

### 2. 创建发布分支

```bash
git checkout -b release/v2.0.0
```

### 3. 提交更改

```bash
git add .
git commit -m "feat: 项目重构为公开发布版本

- 实现 ID-key 数据结构（MD5 8字符）
- 添加完整的环境变量配置
- 规范化所有路径为相对路径
- 创建完整的项目文档
- 添加 .gitignore 和 .env.example
- 修复硬编码路径问题
"
```

### 4. 推送到远程

```bash
git push origin release/v2.0.0
```

### 5. 创建 Pull Request

- 标题：`Release v2.0.0 - 公开发布版本`
- 描述：参考 README.md 中的功能列表
- 审核者：项目维护者

### 6. 合并到主分支

```bash
git checkout main
git merge release/v2.0.0
git tag -a v2.0.0 -m "Release version 2.0.0"
git push origin main --tags
```

## 📦 发布后验证

### 1. 克隆测试

```bash
# 在新目录测试
cd /tmp
git clone <repository-url>
cd comfyui-draw
```

### 2. 按照 README.md 执行

- [ ] 环境配置
- [ ] 依赖安装
- [ ] 服务启动
- [ ] 功能测试

### 3. 文档验证

- [ ] 所有链接可访问
- [ ] 示例命令可执行
- [ ] 配置说明清晰

## 🐛 已知问题

### 需要手动处理的文件

以下文件包含大量映射数据，暂未修改路径：
- `modules/pretags-draw/scripts/translate_cnames.py`（角色名翻译映射）
- `modules/pretags-draw/scripts/translate_cnames2.py`（角色名翻译映射 v2）

**建议**：这些文件主要用于历史数据迁移，如果不需要可以移到 `references/` 目录。

### 环境特定配置

某些功能可能需要额外配置：
- LoRA 模型路径（取决于 ComfyUI 安装位置）
- 预览图生成（需要 PIL/Pillow）
- Excel 导入（需要 openpyxl）

## 📝 版本历史

### v2.0.0 (2026-05-21)

**重大变更：**
- 数据结构从 name-key 迁移到 ID-key（MD5 8字符）
- 项目重构为可公开发布版本
- 完整的环境变量配置系统

**新增功能：**
- 完整的项目文档（README.md, SKILL.md）
- 环境变量模板（.env.example）
- Git 版本控制配置（.gitignore）
- 发布检查清单（本文件）

**修复：**
- 移除所有硬编码的绝对路径
- 规范化为相对路径
- 移除个人信息和敏感数据

**数据迁移：**
- 19,101 个角色记录
- 10,300 个标签记录
- 279 个 LoRA 角色的 appearance/clothing 字段恢复

### v1.x (2026-05-20 之前)

- 原始开发版本
- name-key 数据结构
- 个人使用配置

## 🔗 相关资源

- **项目文档**：[`README.md`](README.md)
- **技能文档**：[`SKILL.md`](SKILL.md)
- **环境配置**：[`.env.example`](.env.example)
- **ComfyUI 文档**：[`comfyui-api/SKILL.md`](modules/comfyui-api/SKILL.md)
- **Civitai 文档**：[`civitai-api/SKILL.md`](modules/civitai-api/SKILL.md)
- **绘图工作流**：[`pretags-draw/SKILL.md`](modules/pretags-draw/SKILL.md)

## ✅ 发布确认

- [ ] 所有检查项已完成
- [ ] 测试通过
- [ ] 文档完整
- [ ] 代码审核通过
- [ ] 准备发布

**发布负责人签名**：_______________  
**发布日期**：_______________  
**版本号**：v2.0.0
