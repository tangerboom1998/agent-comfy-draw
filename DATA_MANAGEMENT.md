# 大型数据文件管理指南

本项目包含大型 pretags 数据文件（约 40MB 总计），你需要决定如何管理这些文件。

## 数据文件清单

- `pretags/pretags-anima.json` - 19MB（Anima 工作流数据）
- `pretags/pretags-ill-noob.json` - 20MB（Illustrious/Noob 工作流数据）

## 三种管理策略

### 选项 1：使用 Git LFS（推荐用于团队协作）

**优点**：
- 数据纳入版本控制
- 不会使仓库体积过大
- 团队成员自动获取最新数据

**缺点**：
- 需要 Git LFS 支持
- 某些平台（如 GitHub）有 LFS 存储限制

**操作步骤**：
```bash
# 1. 安装 Git LFS
# Ubuntu/Debian: sudo apt install git-lfs
# macOS: brew install git-lfs
# Windows: 下载安装包 https://git-lfs.github.com/

# 2. 初始化 Git LFS
git lfs install

# 3. 跟踪 JSON 数据文件
git lfs track "pretags/*.json"

# 4. 提交 .gitattributes
git add .gitattributes
git commit -m "chore: add Git LFS tracking for pretags data"

# 5. 添加并提交数据文件
git add pretags/*.json
git commit -m "chore: add pretags data files via Git LFS"
```

### 选项 2：直接提交到 Git（适合个人项目）

**优点**：
- 简单直接
- 无需额外配置

**缺点**：
- 仓库体积增大 40MB+
- Clone 时间变长
- 每次更新会保留历史版本

**操作步骤**：
```bash
# 1. 从 .gitignore 移除数据文件忽略规则
# 编辑 .gitignore，删除或注释掉：
# pretags/*.json

# 2. 添加并提交
git add pretags/*.json
git commit -m "chore: add pretags data files"
```

### 选项 3：不提交到 Git（推荐用于大型数据集）

**优点**：
- 仓库保持轻量
- 适合频繁更新的数据

**缺点**：
- 需要单独分发数据文件
- 新用户需要额外步骤获取数据

**操作步骤**：
```bash
# 1. 确保 .gitignore 包含数据文件规则
# 已配置（默认注释），取消注释即可：
# pretags/*.json
# pretags/pretags-*.json

# 2. 在 README.md 中说明数据获取方式
# - 提供下载链接（如云盘、CDN）
# - 或提供数据生成脚本
```

## 推荐方案

根据项目类型选择：

| 项目类型 | 推荐方案 | 原因 |
|---------|---------|------|
| 开源团队协作 | Git LFS | 版本控制 + 轻量仓库 |
| 个人项目（数据稳定） | 直接提交 | 简单直接 |
| 个人项目（数据频繁更新） | 不提交 | 保持仓库灵活 |
| 数据集超过 100MB | 不提交 | 避免仓库过大 |

## 当前状态

当前配置：数据文件**未被忽略**（.gitignore 中相关规则已注释）

- ✅ 已创建 `pretags/` 目录
- ✅ 已有 2 个数据文件（约 40MB）
- ⚠️ 数据文件未提交到 Git
- ⚠️ 需要决定管理策略

## 快速决策

**如果你是项目维护者，请执行以下操作之一：**

```bash
# A. 使用 Git LFS（推荐）
git lfs install
git lfs track "pretags/*.json"
git add .gitattributes pretags/*.json
git commit -m "chore: add pretags data via Git LFS"

# B. 直接提交
git add pretags/*.json
git commit -m "chore: add pretags data files"

# C. 不提交（修改 .gitignore）
# 编辑 .gitignore，取消注释：
# pretags/*.json
# 然后在 README.md 添加数据获取说明
```

## 注意事项

1. **首次决策最重要**：一旦提交大文件，从历史记录中移除很困难
2. **GitHub 限制**：单文件不能超过 100MB，仓库建议不超过 1GB
3. **Git LFS 配额**：GitHub 免费账户每月 1GB 流量，每个仓库 1GB 存储
4. **数据更新频率**：如果数据每天更新，不要直接提交到 Git

## 相关文档

- Git LFS 官方文档：https://git-lfs.github.com/
- GitHub 大文件管理：https://docs.github.com/en/repositories/working-with-files/managing-large-files
