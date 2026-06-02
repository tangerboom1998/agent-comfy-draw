# 角色立绘批量生成

> 合并自: character-preview-generation.md, character-preview-batch-generation.md

---

## 背景

为 pretags 中所有角色批量生成预览图（立绘），用于 Tanger-Presets-Show 管理界面展示。

- 总角色数：485 个（含 LoRA）
- LoRA 文件数：162 个
- 162 个 LoRA 覆盖 485 个角色（部分角色共享 LoRA，通过不同服装细分）

## 预览图规格

- 分辨率：1024×1560（竖版立绘）
- 工作流：NoobAI 主工作流
- 每张耗时：~30-40 秒
- 全量生成预估：~3.5 小时（472 张）

## 批量生成脚本

```bash
# 全量生成（用 nohup 避免超时）
nohup python tools/character_preview_gen.py --all > preview_gen.log 2>&1 &

# 自定义采样参数
python tools/character_preview_gen.py --all --steps 20 --cfg 5 --resolution 1024x1560
```

### 脚本逻辑

1. 遍历 pretags.json 中 `characters` 条目
2. 筛选：Lora=1 且 lora_file 非空
3. 构建 prompt：`[角色tags], standing, simple white background, full body, character sheet`
4. 提交 ComfyUI 生成
5. 从 FaceDetailer 输出中选择最佳版本
6. 保存为 JPG 预览图

### 生成参数确认

| 参数 | 推荐值 |
|------|--------|
| Steps | 20-25 |
| CFG | 5-6 |
| Resolution | 1024×1560 |
| Sampler | dpmpp_2m |
| Scheduler | karras |

## 单角色手动生成

### Step 1 — 筛选角色

```bash
# 从 pretags 中选取目标角色
python -c "
import json
with open('pretags.json') as f: d = json.load(f)
targets = [(cid, info) for cid, info in d['characters'].items() if info.get('lora_file')]
print(f'共 {len(targets)} 个有 LoRA 的角色')
"
```

### Step 2 — 构建 prompt

```
masterpiece, best quality, safe,
[角色tags],
standing, simple white background,
full body, character sheet, solo,
```

### Step 3 — 生图

```bash
python comfyui_draw.py --prompt "masterpiece, best quality, safe, [role tags], standing, simple white background, full body, character sheet, solo" --steps 20 --cfg 5
```

### Step 4 — 选择面部修复图

FaceDetailer 管线输出规则：
- `CCUI_xxx_0.png` — 原始生成图
- `CCUI_xxx_2.epng` — FaceDetailer 处理后（加密PNG）

选择 FaceDetailer 版本（`_2.epng`）作为预览图。

### Step 5 — 保存预览图

```python
# PNG→JPG 转存
from PIL import Image
img = Image.open('CCUI_xxx_2.epng')
img.convert('RGB').save('previews/char_xxx.jpg', quality=85)

# 更新 pretags.json
data['characters'][cid]['preview'] = 'previews/char_xxx.jpg'
```

## 常见陷阱

### 1. 非 LoRA 角色：必须用 name 字段补充角色身份

```python
# ❌ 错误 — 少了角色身份 tag
prompt = "masterpiece, best quality, safe, standing, white background"

# ✅ 正确
prompt = f"masterpiece, best quality, safe, {info['name']}, {info['tags']}, standing, white background"
```

### 2. 父条目 vs 细分条目（多服装混合）

同一 LoRA 文件可能对应多个角色（服装变体）。父条目应跳过，只为子条目（有明确服装 tag 的）生成预览。

### 3. Web 端保存会丢失 preview 字段

Tanger-Presets-Show Web 界面保存时不会保留 `preview` 字段。修改 preview 应通过 CLI/Python 直接操作 pretags.json。

### 4. LoRA 格式：无后缀、无目录前缀

```python
# ✅ 正确
lora_file = "my_character.safetensors"

# ❌ 错误
lora_file = "人物/my_character.safetensors"
lora_file = "my_character"
```

### 5. sclaw311 环境缺少 PIL

```bash
# 修复（在 sclaw311 环境下）
pip install Pillow
```

### 6. Hermes 后台进程超时（SIGTERM exit 143）

nohup 进程在 Hermes 中可能被 SIGTERM 终止。解决方案：
- 使用 `tmux` 或 `screen` 会话
- 分批处理（每批 50 个）

```bash
# 查看当前在跑哪张
tail -f preview_gen.log
```

### 7. 慎用 bare `python`（环境选择）

```bash
# ❌ 错误（可能走 base 环境，缺 PIL）
python tools/preview_gen.py

# ✅ 正确（指定 conda 环境）
~/anaconda3/envs/sclaw311/bin/python tools/preview_gen.py
```

## 手动替换预览图（外部图片）

当收到外部图片作为预览图时：

1. 保存图片到 `previews/` 目录
2. 用 PIL 转存为 JPG（统一格式）
3. 更新 pretags.json 中的 `preview` 字段

```python
from PIL import Image
# 用 sclaw311 环境的 PIL 转存为 JPG
img = Image.open('received_image.png')
img.convert('RGB').save('previews/char_xxx.jpg', quality=85)

# 更新 pretags.json
import json
with open('pretags.json') as f:
    data = json.load(f)
data['characters'][char_id]['preview'] = 'previews/char_xxx.jpg'
with open('pretags.json', 'w') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

## 执行记录

- 2026-05-17 批量运行：273 张，40 分钟完成
- 2026-05-20 补充：约 200 张
- 单张测试 — 琪亚娜白练：成功
- 批量验证 — 尤诺、伊涅芙：成功
