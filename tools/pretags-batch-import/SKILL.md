---
name: pretags-batch-import
description: 分批模型下载→标签拆分→pretags入库完整流水线。每批5-15个模型，Phase 1~5完整闭环后才进入下一批。核心解决了CivitAI trainedWords 中服装/外貌标签混杂的问题。

references:
  - references/pretags-supplement-workflow.md
  - references/pretags-patch-pitfalls-2026-05.md
  - references/artstyle-batch-import-2026-05.md
  - scripts/fix_pretags_lora.py
---

# Pretags 分批入库流水线

## 核心原则

- **分批进行**：每批 5-15 个模型，Phase 1→5 完整闭环后才进入下一批
- **公子在批次间可随时喊停、复查、调整**
- **标签分类优先级**：外貌和服装必须分开，不得混入同一字段
- **禁止全量操作**：不允许一次性下载/处理所有模型再统一入库

---

## 批量处理流程

```
公子指定一批模型（按 creator + newest 过滤，或手动列出）
    ↓
┌─────────────────────────────────────────┐
│ Phase 1 · 发现与清单                      │
│ ├─ civitai-api 批量获取模型元数据          │
│ ├─ 提取 trainedWords / hash / 来源游戏     │
│ └─ 产出：批次清单（模型名、hash、link）     │
├─────────────────────────────────────────┤
│ Phase 2 · 下载                           │
│ ├─ 逐条对比本地 hash（AutoV2 前缀匹配）     │
│ ├─ 跳过已存在 → 仅下载缺失                  │
│ ├─ ⚠️ 文件名必须与 pretags.json 中一致     │
│ └─ 下载到 loras/人物/                     │
├─────────────────────────────────────────┤
│ Phase 3 · 标签拆分 ★ 核心                  │
│ ├─ 对每条 trainedWords 逐 tag 审核         │
│ ├─ 按分类规则拆分外貌 vs 服装               │
│ ├─ 去污染（见下方）                        │
│ └─ 产出：拆分后的外貌/服装标签              │
├─────────────────────────────────────────┤
│ Phase 4 · 入库 pretags                    │
│ ├─ 构建完整条目（含 hash/link/Source）      │
│ ├─ 逐条用 patch 写入 pretags.json         │
│ ├─ 每条写入后 JSON 验证                   │
│ └─ ⚠️ old_string 必须同时匹配外貌+服装两行  │
├─────────────────────────────────────────┤
│ Phase 5 · 验证                           │
│ ├─ 每角色 tag_producer 测试一次            │
│ ├─ hash 对比确认                          │
│ └─ 批次总结报告                           │
│                                          │
│ ⏸️ 等公子确认 → 下一批                     │
└─────────────────────────────────────────┘
```

---

## 多角色模型拆分规则（强制）

当一个 LoRA 文件包含多个角色时（如 `granblue_fantasy_all` 包含 50+ 碧蓝幻想角色）：

1. **每个角色拆为独立 pretags 条目**，共用同一个 `model file name`
2. **每个角色的 `name` 字段 = 该角色的触发词**（如 `narmaya_(granblue_fantasy)`）
3. **泳装/变体服装版本必须独立建条目**，不与默认服装版本合并。如 `Anila` 和 `Anila泳装` 是两条独立记录
4. 变体条目的 `cname` 格式：`角色名泳装` / `角色名变体名`（如 `Narmaya泳装`、`Fighter(Djeeta)`）

```
❌ 错误：一个条目覆盖所有角色（触发词 "all in one"）
❌ 错误：泳装版本合并到默认服装条目
✅ 正确：每个角色+每个服装变体 = 独立条目
```

## Phase 3 标签分类规则（强制）

### 归入「外貌」
种族/物种、发色/发型、瞳色/瞳孔特征、角/耳/尾/翅膀、体型特征、面部特征（ahoge/facial mark）、纹身/身体标记、光环

### 归入「服装」
衣物（dress/suit/kimono）、鞋袜（boots/thighhighs）、手套、头饰（hair ornament/hat/beret）、首饰（earrings/bracelet/necklace）、腿环/吊带（thigh strap/garter）、眼罩/眼镜

### 边界判定速查
| 标签 | 去向 | 理由 |
|------|------|------|
| `horns` `antlers` | 外貌 | 身体部位 |
| `bare shoulders` | 外貌 | 身体裸露状态 |
| `halo` | 外貌 | 非穿戴物 |
| `see-through` `see-through legs` | 服装 | 衣物透视效果 |
| `tentacles` | 外貌 | 身体部位 |
| `hair ornament` | 服装 | 头上佩戴的饰品 |
| `thigh strap` `garter` | 服装 | 穿戴物 |
| `netting eye mask` | 服装 | 穿戴物 |
| `tattoo` `markings` | 外貌 | 身体标记 |

### 去污染清单（必须移除）
| 污染类型 | 示例 | 处理 |
|----------|------|------|
| 场景标签 | `white background` | ❌ 删除 |
| 画风标签 | `science fiction` | ❌ 删除 |
| 负向提示 | `(no weapon:1.3)` | ❌ 删除 |
| 触发词前缀 | `Xxxdef`, `Xxxbig`, `Xxxlover` | ✂️ 剥离后保留真实 tag |
| 重复标签 | 同一条目出现相同 tag 两次 | ❌ 删除重复项 |

### 触发词前缀剥离规则
CivitAI trainedWords 中常见格式：

| 格式 | 示例 | 解析 |
|------|------|------|
| `XxxdefTAG` | `Galbrenadef,` | 裸触发前缀，删除 |
| `Xxxdef TAG` | `Yvonne def multicolored clothes` | 去掉 `Xxxdef ` 前缀，保留 `multicolored clothes` |
| `Xxxbig TAG` | `Cyrenebig white-and-purple dress` | 去掉 `Xxxbig `，保留 `white-and-purple dress` |
| `Xxxlover TAG` | `Elysialover red-and-white dress` | 去掉 `Xxxlover `，保留 `red-and-white dress` |
| `Xxx's TAG` | `Laevatain's horns` | 去掉所属关系，保留 `horns` |

**统一做法**：识别 `[角色名]def/big/lover` 前缀 → 剥离 → 留下纯英文 tag。

---

### Phase 4 写入规范

**⚠️ 画风描述特殊规则：** artstyle 类型的 `description` 字段**禁止**直接使用 Civitai API 抓取的 description/trainedWords。必须通过本地生图实测 → vision 分析来撰写画风描述（详见 `artstyle-test` skill）。Civitai 元数据仅用于获取 hash、版本信息等结构化数据。

### 画风条目补充规则
- 盘点目标目录内未入库 `.safetensors` 时，用 `model file name` 对比必须统一为**不带扩展名的 stem**。
- 新增 `画风` 条目时，`model file name` **只能写 stem，不要写 `.safetensors` 扩展名**。
- 每轮批处理前，先快速巡检 `pretags.json` 里的本类条目；如果发现 `model file name` 被写成 `xxx.safetensors`，必须先归一化再继续统计，否则会把已录入模型误判成未录入。
- 对明显不是画风 LoRA 的条目（例如角色包、多角色角色集合）不要硬塞进 `画风` 分类；先跳过并单独记账。
- 对 SSL EOF、timeout、remote close、404 等 by-hash 异常，先记账继续推进别的条目，后续再回头重试。

### 画风条目：CivitAI 未命中时的入库策略
当 by-hash 返回 `{"error":"Model not found"}` 时，仍然入库：
- `link` 填 `无`
- `tag` 填 `无`
- `model hash` **正常填**（作为去重依据）
- `画风描述` **留空 `""`**（禁止填占位描述；画风描述仅在后续实际生图测评中产生，不得从 Civitai API 抓取描述文字直接写入）

用户明确要求：目录下的文件默认都是画风模型，CivitAI 没有也要入库，不能跳过。参见 `references/artstyle-batch-import-2026-05.md`。

### 画风批处理 Pitfalls
- **格式污染陷阱**：`model file name` 混用 stem 与 `stem.safetensors` 两种格式，会导致剩余数量统计严重虚高，自动批处理反复把已录入文件当成未录入。每次批处理开始前，先巡检并归一化。
- **目录即分类规则**：当用户明确说 `$LORA_MODEL_DIR/{model_type}/画风` 目录下默认全是画风模型时，按目录范围优先，不要再因为名字像角色包、合集包或命名古怪就先跳过；只有在 CivitAI by-hash 多次失败时才挂阻塞。
- **路径配置**：所有路径通过 `LORA_MODEL_DIR` 和 `COMFYUI_ROOT` 环境变量配置（在 `.env` 中设置）。Python 脚本通过项目根 `_env.py` 统一获取。目录结构为 `$LORA_MODEL_DIR/{model_type}/{category}/`，model_type 由文件名关键字自动检测。
- **进度判断陷阱**：自动任务 `last_status=ok` 不代表统计口径正确；当剩余数异常不降时，要优先检查 `model file name` 规范，而不是先怀疑 CivitAI 没推进。
- **慢任务切换策略**：如果 cron/后台任务推进过慢，用户要求停掉时，应暂停自动任务，改回手动分批推进，不要坚持慢速自动化。
- **CivitAI "Model not found" 回退策略**：当 by-hash 返回 `{"error":"Model not found"}` 时，不代表该文件不该入库。用户明确要求：CivitAI 没有的模型也要入库，`link` 和 `tag` 填 `无`，`model hash` 正常填（作为去重依据）。不要因为 404 就跳过。
- **cron vs 手动的速度差异**：自动 cron 任务每轮有 agent 启动开销 + 逐条 API 调用延迟，处理 12 个条目可能要 10-20 分钟；手动批量处理同样的 12 个可以在 2-3 分钟内完成。当用户要求"快速推进"时，优先用手动分批而不是 cron。
- **Safetensors metadata tag recovery**：当 `tag = "无"` 时，可以从 `.safetensors` 文件的 `ss_tag_frequency` 元数据中提取训练 tag 频率，过滤掉通用标签后取 top 8 作为该模型的触发词。参见 `references/artstyle-batch-import-2026-05.md`。
- **Corrupted file re-download**：如果下载文件大小明显偏小（如 3.9MB vs 预期 218MB），删除后用 `civitai.py download-model` 重新下载，然后 hash 校验确认。

---

## 画风 Lora 标记批量修正

### 触发场景
磁盘上有 `.safetensors` 模型文件，对应的 pretags 条目也存在，但 `Lora` 字段为 `0`（而非 `1`）。常见于批量导入后的遗留维护环节——条目已入库但 Lora 标志没有同步更新。

### 判断流程（避免陷阱 5）
```
加载 pretags.json → 收集画风分类所有条目的 model file name（不限 Lora）。
扫描磁盘画风目录 → 收集所有 .safetensors 的 stem。
三向集合运算：
  A = disk_stems（磁盘）
  B = all_pretags_stems（pretags 全部条目）
  C = lora1_pretags_stems（pretags 中 Lora=1 的条目）

真正未入库 = A - B
需修正 Lora = (A ∩ B) - C   ← 这才是批量修正的目标
```

### 使用脚本
```bash
cd tools/pretags-batch-import
python3 scripts/fix_pretags_lora.py
```
自动备份 → 比对 → 修正 → 验证。详见 `scripts/fix_pretags_lora.py`。

### 修正后验证
1. 确认 `lora1_after` 总数 ≥ 磁盘文件数
2. 确认 `lora0_after` 中再无条目指向磁盘上存在的文件
3. 确认备份文件存在可回滚

### 画风批处理 Verification
- 每轮入库后先 `json.load` 校验 `pretags.json`。
- 用磁盘 stem（不带 `.safetensors`）对比 `画风` 条目里的 `model file name`，重新计算真实 remaining。
- 如果刚新增某个条目，复核它的 stem 已进入 registered 集合后再汇报进度。

### 人物条目完整模板
```json
{
    "cname": "中文名",
    "Source": "来源游戏",
    "Lora": 1,
    "model file name": "文件名（与.safetensors一致，不含路径）",
    "unet weight": 0.8,
    "clip weight": 0.8,
    "link": "https://civitai.com/models/XXXXX",
    "model hash": "AABBCCDDEE",
    "name": "触发词 \\(游戏名\\)",
    "外貌": "1girl, hair_color, eye_color, ...",
    "服装": "dress_type, accessories, ..."
}
```

### patch 操作注意事项
- **old_string 必须同时包含外貌行和服装行**，否则会出现重复 `服装` 字段
- 错误示例：仅匹配 `"外貌": "..."` → 新服装字段写入后旧 `"服装": ""` 残留
- 正确示例：`"外貌": "旧标签",\n      "服装": ""` → 一行匹配两字段

---

## 常见陷阱

### 陷阱 1：CivitAI 元数据不足以区分标签
**现象**：`trainedWords` 把所有标签混在一个数组/字符串中，无外貌/服装标记。
**修复**：必须 Phase 3 手动逐条审核拆分，不可依赖 API 自动分类。

### 陷阱 2：Hash 对比需用前缀匹配
**现象**：CivitAI API 返回完整 SHA256，pretags 存前 10 位，`==` 永远不匹配。
**修复**：使用 AutoV2 前缀匹配。

### 陷阱 3：patch 造成重复字段
**现象**：`"服装"` 字段出现两次，JSON 解析报错。
**修复**：old_string 必须包含 `"服装": ""` 行。出问题后立即回滚修复。

### 陷阱 4：def 前缀格式不统一
**现象**：有的 `Xxxdef TAG`（有空格），有的 `XxxdefTAG`（无空格），有的 `Xxxdef,`（裸逗号）。
**修复**：三种情况都要处理。

### 陷阱 5：磁盘 vs pretags 差异对比时 Lora 盲区
**现象**：对比脚本只收集 `Lora==1` 的 `model file name`，然后发现「磁盘文件数 > pretags Lora=1 数」，就误报"N 个文件未入库"。实际上那些文件在 pretags 里存在，只是 `Lora=0`。
**用户反应**：直接质疑"你确定？"——如果对比口径不对，用户一眼就能看出数据矛盾，造成信任危机。
**修复**：差异对比必须收集**全部条目**（不限 Lora 值）的 `model file name` 与磁盘 stem 做集合差。只有 `disk_stems - all_pretags_stems` 才是真正的未入库文件。Lora 标志是状态属性，不能反向推导"Lora≠1 就没记录"。
**验证手段**：如果报告"未入库"数量很大（>50），先跑一次三向交叉检验（disk_stems vs all_pretags_stems vs lora1_pretags_stems），确认问题性质后再汇报。

---

## 🎨 画风描述规范（强制）

**画风描述字段不得使用 CivitAI API 抓取的描述文字。** 无论是模型说明、作者描述、版本说明还是 HTML 富文本，一律不准直接写入 `画风描述` 字段。

**画风描述的唯一来源是本地生图评测：**
1. 用 ComfyUI 生成测试图（人物 / 场景 / 人物+场景）
2. 用 vision 模型分析色调、笔触、光影、质感、线条、风格关键词
3. 基于实测结果撰写 50-80 字中文描述
4. 写入 `画风描述` 字段

**导入新画风模型时，`画风描述` 必须留空 `""`，等后续实测后填入。**

详见 `comfyui-draw` 技能中的「画风测试工作流」和 `references/artstyle-description-cleanup.md`。

---

## 批次报告模板

每批完成后输出：
```
## 📊 批次 N 完成报告
| 模型 | Hash | 外貌tags | 服装tags | 去污染 | 状态 |
|------|------|----------|----------|--------|------|
| xxx  | xxxx | N        | N        | N      | ✅   |

总计：N✅ / N⚠️ / N 条
```
