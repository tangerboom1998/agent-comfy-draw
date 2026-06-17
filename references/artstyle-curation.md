# 画风管理与测试

画风 LoRA 的整理、测试和描述生成流程。

## 核心概念

- **画风 LoRA** - 用于控制生图风格的模型
- **实测评估** - 通过实际生图和 Vision 分析确定画风特征
- **描述生成** - 基于实测结果编写画风描述

## 使用场景

### 场景 1: 画风测试

**步骤**:
1. 使用固定 base prompt 生成测试图
2. Vision 分析画风特征
3. 编写简洁的画风描述（30-80字）
4. 写入 pretags.json

**示例**:
```bash
# 生成测试图
python comfyui_draw.py "1girl, solo, white dress, standing" \
  --lora "<lora:style_name:0.8:0.8>" --canvas 竖图

# 分析后写入描述
python update_style_description.py "style_name" \
  "厚涂赛璐璐混合风，线条粗犷有力，色彩饱和度高"
```

### 场景 2: 批量测试

**批量处理流程**:
1. 查询待测画风（`画风描述` 为空）
2. 逐个生成测试图
3. Vision 并行分析
4. 批量写入描述

**示例**:
```bash
cd tools/artstyle-test/scripts
python artstyle_rerun.py --start 0 --limit 15
```

### 场景 3: 画风整理

**文件管理**:
1. 统计磁盘上的画风文件
2. 对比 pretags.json 中的记录
3. 补全缺失的画风条目
4. 清理无效文件

## 注意事项

- ⚠️ 画风描述必须来自实测，不要直接使用 Civitai 描述
- ⚠️ LoRA 格式：`<lora:filename:0.8:0.8>`（不要省略 clip 权重）
- ⚠️ 测试时使用通用 prompt，避免角色特征干扰

更多警告见：[WARNINGS.md](warnings.md)

## 相关文档

- [画风测试工具](../tools/artstyle-test/SKILL.md)
- [Pretags 数据管理](./pretags-data-management.md)

---

**最后更新**: 2026-06-07
