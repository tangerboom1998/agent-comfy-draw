# References 目录审查报告

**审查日期**: 2026-06-07
**当前文件数**: 13 个

---

## 📊 文档分类

### ✅ 保留（核心文档）

这些是必需的、有效的核心参考文档：

1. **workflow-node-mapping.md** (161 行) - ✅ 刚创建，简洁有效
   - 工作流节点 ID 映射表
   - 三种工作流类型识别

2. **pretags-draw-rules.md** (206 行) - ✅ 刚创建，简洁有效
   - Pretags Draw 使用规则
   - 提示词构建规范

3. **comfyui-pitfalls.md** (143 行) - ✅ 保留
   - ComfyUI 常见问题和解决方案
   - Host URL 配置问题

### 🔄 需要精简（内容过长或重复）

4. **anima-prompt-and-workflow.md** (323 行) - ⚠️ 过长
   - 合并了 5 个文档，内容冗余
   - 建议：精简到 150 行以内，移除重复内容

5. **artstyle-curation.md** (245 行) - ⚠️ 过长
   - 合并了 5 个文档
   - 建议：精简到 100 行，保留核心流程

6. **character-preview-generation.md** (187 行) - ⚠️ 过长
   - 建议：精简到 80 行

7. **pretags-data-management.md** (266 行) - ⚠️ 过长
   - 合并了 5 个文档
   - 建议：精简到 150 行

8. **pretags-excel-workflow.md** (231 行) - ⚠️ 过长
   - 合并了 3 个文档
   - 建议：精简到 120 行

9. **z-image-guide.md** (249 行) - ⚠️ 过长
   - 合并了 3 个文档
   - 建议：精简到 150 行

10. **safetensors-tag-recovery.md** (384 行) - ⚠️ 过长
    - 建议：精简到 150 行或拆分

### ❓ 评估是否必需

11. **environment-setup.md** (188 行) - ❓
    - 环境变量和目录布局
    - 评估：部分内容可能已过时，需要验证

12. **docker-sandbox-guide.md** (103 行) - ❓
    - Docker Sandbox 配置
    - 评估：是否仍在使用？

13. **face-detailer-pipeline.md** (114 行) - ❓
    - FaceDetailer 节点结构
    - 评估：是否可以合并到 workflow-node-mapping.md

---

## 🎯 清理计划

### 阶段 1: 立即删除/合并（减少文件数）

**方案 A：激进清理（推荐）**
- 删除：face-detailer-pipeline.md → 合并到 workflow-node-mapping.md
- 删除：docker-sandbox-guide.md → 移至 WARNINGS.md（如仍需要）
- 保留核心：10 个文档

**方案 B：保守清理**
- 全部保留，只精简内容

### 阶段 2: 精简每个文档

**目标**：
- 每个文档 ≤ 150 行
- 移除重复内容
- 移除过时信息
- 移除冗长的示例代码

**精简原则**：
1. 只保留**核心流程**和**关键决策点**
2. 移除详细的代码实现（应在代码中体现）
3. 移除历史记录和时间戳
4. 移除"合并自"这类元信息

### 阶段 3: 标准化格式

所有 reference 文档统一格式：

```markdown
# 文档标题

简短说明（1-2 句话）。

## 核心概念/流程

- 要点 1
- 要点 2
- 要点 3

## 使用场景

### 场景 1

简短说明 + 关键步骤（3-5 步）

### 场景 2

...

## 注意事项

仅列出 2-3 条最关键的注意事项。

## 相关文档

- [相关 SKILL](../modules/xxx/SKILL.md)
- [相关 reference](./yyy.md)
```

---

## 📋 优先级

### 高优先级（立即处理）

1. **创建 WARNINGS.md** - 存放所有警告和注意事项
2. **精简过长文档**（>200 行的 7 个文档）
3. **删除/合并冗余文档**（face-detailer, docker-sandbox）

### 中优先级

4. **标准化所有文档格式**
5. **验证内容准确性**
6. **更新交叉引用链接**

### 低优先级

7. **检查代码示例是否仍然有效**
8. **补充缺失的用例**

---

## 📊 预期成果

**Before**:
- 13 个文档
- 总计约 2,800 行
- 部分文档 >300 行
- 内容重复、过时

**After**:
- 10-11 个文档（减少 2-3 个）
- 总计约 1,200-1,500 行（减少 50%）
- 每个文档 ≤150 行
- 内容简洁、准确、有效

---

## 🚀 下一步行动

1. **创建 WARNINGS.md**
2. **精简 top 3 最长的文档**：
   - safetensors-tag-recovery.md (384→150 行)
   - anima-prompt-and-workflow.md (323→150 行)
   - pretags-data-management.md (266→150 行)
3. **删除/合并冗余文档**
4. **创建 REFERENCE_TEMPLATE.md** 标准模板

---

**审查人**: Claude Code Assistant
**下一步**: 获取用户确认后开始清理
