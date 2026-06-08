# 三种模型的提示词差异对比

Anima (Flux)、SDXL (Illustrious/Noob)、z-image Turbo 三种模型的提示词编写差异说明。

---

## 📊 核心差异对比表

| 特性 | Anima (Flux) | SDXL (Illustrious/Noob) | z-image Turbo |
|------|-------------|------------------------|---------------|
| **架构** | Flux | SDXL | Flux Turbo |
| **大小写** | 全小写 | 不敏感 | 全小写 |
| **分隔符** | 逗号+空格 | 逗号+空格 | 逗号+空格 |
| **LoRA 支持** | ❌ 不支持 SDXL LoRA | ✅ 支持 SDXL LoRA | ❌ 不支持 SDXL LoRA |
| **质量前缀** | masterpiece, best quality, newest, latest | masterpiece, best quality | 可选 |
| **画师标签** | `@wlop` 格式 | `wlop` 或 `@wlop` | `@wlop` 格式 |
| **Steps** | 28-40 | 20-30 | 4-8 (Turbo) |
| **CFG** | 5.5-7.0 | 5.0-7.0 | 1.0 |
| **特殊标签** | `safe,` / `nsfw,` | 无特殊要求 | 无特殊要求 |

---

## 🎯 详细对比

### 1. Anima (Flux 架构)

**模型特点**:
- 基于 Flux 架构，最新的扩散模型
- 不支持 SDXL LoRA
- 对提示词格式较为严格

**提示词规范**:

```
标准格式（全小写，逗号空格分隔）：
masterpiece, best quality, newest, latest, safe,
@wlop, @ask,
1girl, solo, long hair, blue eyes, silver hair,
white dress, bare shoulders,
standing, looking at viewer,
castle background, moonlight, night sky,
soft lighting, dreamlike atmosphere
```

**关键要求**:
1. **全小写** - 所有标签必须小写
2. **质量标签必备** - `masterpiece, best quality, newest, latest`
3. **Safe 标签** - SFW 内容必须加 `safe,`，NSFW 加 `nsfw,`
4. **画师格式** - 使用 `@artist_name` 格式
5. **严格顺序** - 质量 → 安全 → 画师 → 角色 → 动作 → 场景 → 光影
6. **不支持 LoRA** - 不能使用 `<lora:xxx>` 标签

**推荐参数**:
- Steps: 28-40
- CFG: 5.5-7.0
- Sampler: dpmpp_2m
- Resolution: 1024×1024 或 1024×1536

---

### 2. SDXL (Illustrious/Noob)

**模型特点**:
- 基于 SDXL 架构，成熟稳定
- 完整支持 SDXL LoRA
- 提示词格式相对宽松

**提示词规范**:

```
标准格式（大小写不敏感）：
masterpiece, best quality,
<lora:character_noob:0.9:0.9>,
<lora:style_noob:0.7:0.7>,
1girl, solo, Long Hair, Blue Eyes,
White Dress, bare shoulders,
standing, looking at viewer,
castle background, night sky,
```

**关键要求**:
1. **大小写不敏感** - `1girl` 和 `1Girl` 都可以
2. **LoRA 支持** - 支持 `<lora:filename:unet_weight:clip_weight>` 格式
3. **质量标签** - `masterpiece, best quality` 足够
4. **画师标签** - `wlop` 或 `@wlop` 都可以
5. **顺序灵活** - 不强制要求严格顺序
6. **Danbooru 标签** - 与 Danbooru 标签体系完全兼容

**推荐参数**:
- Steps: 20-30
- CFG: 5.0-7.0
- Sampler: dpmpp_2m 或 euler_a
- Resolution: 1024×1024 或 832×1216

**LoRA 格式**:
```
<lora:filename:0.8:0.8>
        ↑    ↑   ↑   ↑
        |    |   |   └─ CLIP 权重
        |    |   └───── UNET 权重
        |    └───────── 文件名（不含 .safetensors）
        └────────────── 固定格式
```

---

### 3. z-image Turbo

**模型特点**:
- 基于 Flux Turbo 架构
- 4 步快速生图
- 简化的提示词要求

**提示词规范**:

```
简化格式（全小写）：
1girl, solo, long hair, blue eyes,
white dress, standing,
castle background, night
```

**关键要求**:
1. **全小写** - 与 Anima 相同
2. **简洁为主** - 不需要冗长的质量标签
3. **CFG=1** - 固定使用 CFG 1.0
4. **4 步出图** - Steps 固定为 4
5. **快速生成** - 适合批量快速预览
6. **不支持 LoRA** - 与 Anima 相同

**推荐参数**:
- Steps: 4（固定，Turbo 特性）
- CFG: 1.0（固定）
- Sampler: res_multistep
- Scheduler: simple
- Resolution: 1280×1280

---

## 🔄 跨模型提示词转换

### Anima → SDXL

**需要修改**:
1. 移除 `newest, latest, safe` 等 Anima 特有标签
2. 移除画师的 `@` 前缀（可选）
3. 可以添加 LoRA 标签
4. 大小写可以随意

**示例**:
```
# Anima
masterpiece, best quality, newest, latest, safe,
@wlop, 1girl, solo, long hair

# SDXL
masterpiece, best quality,
<lora:style_noob:0.7:0.7>,
wlop, 1girl, solo, long hair
```

### SDXL → Anima

**需要修改**:
1. 移除所有 LoRA 标签
2. 添加 `newest, latest, safe`
3. 转换为全小写
4. 画师添加 `@` 前缀
5. 调整标签顺序

**示例**:
```
# SDXL
masterpiece, best quality,
<lora:character_noob:0.9:0.9>,
wlop, 1Girl, Solo, Long Hair

# Anima
masterpiece, best quality, newest, latest, safe,
@wlop, 1girl, solo, long hair
```

### 任意模型 → z-image Turbo

**需要修改**:
1. 移除所有质量前缀（可选保留）
2. 移除所有 LoRA 标签
3. 简化为核心描述
4. 转换为全小写

**示例**:
```
# SDXL/Anima
masterpiece, best quality, newest, latest,
<lora:xxx:0.8>,
1girl, solo, long hair, blue eyes, white dress, standing

# z-image Turbo
1girl, solo, long hair, blue eyes, white dress, standing
```

---

## 📋 常见错误

### ❌ Anima 使用 SDXL LoRA

```
# 错误
masterpiece, best quality,
<lora:character_sdxl:0.9:0.9>,
1girl, solo

# 结果：LoRA 不生效，可能报错
```

### ❌ SDXL 使用 Anima 的 safe 标签

```
# 不推荐
masterpiece, best quality, safe, newest, latest,
1girl, solo

# 推荐
masterpiece, best quality,
1girl, solo
```

### ❌ z-image 使用高 CFG

```
# 错误
--steps 4 --cfg 7.0

# 结果：图像质量下降

# 正确
--steps 4 --cfg 1.0
```

---

## 🎯 如何选择模型？

### 选择 Anima
- ✅ 需要最新的 Flux 架构效果
- ✅ 追求最高图像质量
- ✅ 不依赖 LoRA
- ❌ 不需要角色 LoRA

### 选择 SDXL (Illustrious/Noob)
- ✅ 需要使用角色/画风 LoRA
- ✅ 需要精确控制角色特征
- ✅ 有大量现成的 SDXL LoRA 资源
- ✅ 追求稳定性和兼容性

### 选择 z-image Turbo
- ✅ 需要快速预览
- ✅ 批量生成测试图
- ✅ 对质量要求不高
- ✅ 追求速度（4 步 vs 28 步）

---

## 📚 相关文档

- [Anima Prompt 指南](./anima-prompt-and-workflow.md)
- [z-image 工作流](./z-image-guide.md)
- [工作流节点映射](./workflow-node-mapping.md)
- [Pretags Draw](../modules/pretags-draw/SKILL.md)

---

**最后更新**: 2026-06-08
