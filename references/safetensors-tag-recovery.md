# Safetensors 元数据 Tag 提取

从 `.safetensors` 文件的元数据中提取训练标签，用于 CivitAI API 无法提供标签时的备选方案。

## 核心概念

- **ss_tag_frequency** - Safetensors 文件元数据中记录的训练标签频率
- **Bucket 结构** - 标签按 bucket 分组存储
- **用途** - 当 CivitAI `by-hash` 或 `trainedWords` 不可用时的备选数据源

## 使用场景

### 场景 1: 提取标签

**步骤**:
1. 使用 `safetensors` 库读取文件元数据
2. 解析 `ss_tag_frequency` 字段
3. 合并所有 bucket 的标签频率
4. 按频率排序

**示例**:
```python
from safetensors import safe_open
import json

def extract_tags(path):
    with safe_open(path, framework="numpy") as f:
        meta = f.metadata()
    tag_freq_raw = meta.get("ss_tag_frequency", "{}")
    tag_freq = json.loads(tag_freq_raw)
    
    # 合并所有 bucket
    all_tags = {}
    for bucket_tags in tag_freq.values():
        for tag, count in bucket_tags.items():
            all_tags[tag] = all_tags.get(tag, 0) + count
    
    return sorted(all_tags.items(), key=lambda x: -x[1])
```

### 场景 2: 按模型类型清理标签

**画风模型**:
- 保留: 触发词、风格关键词、画师名
- 过滤: 通用 booru 标签（1girl, solo, long_hair 等）

**角色模型**:
- 保留: 角色特征标签（发色、瞳色、服装）
- 过滤: 场景、姿势、视角标签

**步骤**:
1. 提取所有标签
2. 根据模型类型应用过滤规则
3. 按频率阈值过滤（通常 >10%）
4. 手动审核高频标签

## 注意事项

- ⚠️ 元数据可能不存在或格式异常
- ⚠️ 需要手动审核和分类，自动化容易出错
- ⚠️ 不同训练方法的元数据结构可能不同

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags 批量导入](../tools/pretags-batch-import/SKILL.md)
- [Pretags 数据管理](./pretags-data-management.md)

---

**最后更新**: 2026-06-07
