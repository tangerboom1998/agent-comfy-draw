# Anima Prompt 与工作流指南

Anima 模型（Flux 架构）的提示词编写规范和工作流配置。

## 核心概念

- **Flux 模型** - Anima 使用 Flux 架构，不兼容 SDXL LoRA
- **语义理解强** - 支持 tag、短句、描述性段落
- **自然语言优先** - 可以用描述性段落替代纯 tag
- **画师必须加 @** - `@wlop`, `@big chungus`
- **全小写** - 所有标签使用小写，逗号空格分隔
- **仅英文** - 不支持中文

## Prompt 编写规范

### 标签顺序（纯 tag 模式）

```
质量标签 → 画师标签 → 角色描述 → 动作/姿势 → 场景/背景 → 光影
```

### 推荐前缀

**正面提示词**:
```
masterpiece, best quality, newest, latest, safe,
```

**负面提示词**:
```
lowres, worst quality, bad anatomy, bad hands, 
blurry, signature, watermark,
```

## 🎨 Anima 高级提示词模板

Anima 支持自然语言描述，使用**结构化单段落模板**可获得高质量输出。

### 模板本体（单段落，无固定格式）

```
画面主体为（角色身份/种族/类型），具备（发色与发型）及（标志性特征），当前处于（衣物覆盖状态或裸露程度）。皮肤质感偏向（光泽/纹理/色调），（关键躯干区域）轮廓（形态描述），（核心细节部位）的刻画呈现（精细度倾向）。构图采用（镜头视角），人物以（基本站位/群像分布）排列，（方位1）的角色呈（姿态趋势），（局部动作）与（方位2）的角色形成（互动方式），（肢体走向）引导视线向（视觉重心）汇聚。背景为（环境类型），（前景/中景元素）以（空间关系）衬托主体，（光源方向）投射出（明暗对比层次）。整体采用（艺术风格），线条处理偏向（特点），色彩搭配遵循（主色调与点缀逻辑），通过（光影渲染技法）强化（整体氛围）。
```

### 占位符填写指南

| 占位符位置 | 需明确的内容方向 | 填写示例 |
|------------|------------------|----------|
| （角色身份/种族/类型） | 主体基础设定 | 科幻女骑士 / 日系JK少女 / 精灵族施法者 |
| （发色与发型） | 头部视觉标识 | 银白色高马尾 / 深棕色微卷长发 |
| （标志性特征） | 区别于常人的特殊部位 | 机械义肢 / 兽耳与尾巴 / 悬浮光环 |
| （衣物覆盖状态或裸露程度） | 躯干遮挡范围 | 半露肩紧身战衣 / 全身裸露 / 轻透薄纱覆盖 |
| （关键躯干区域） | 视觉重心部位 | 胸部与腰腹 / 大腿与膝盖 / 背部与肩胛 |
| （形态描述） | 该区域的体积/线条特征 | 饱满圆润 / 修长流畅 / 紧致分明 |
| （核心细节部位） | 需突出的微观结构 | 乳头 / 关节褶皱 / 机械接缝 |
| （精细度倾向） | 该部位的渲染级别 | 清晰可见 / 轮廓隐约 / 自然过渡 |
| （镜头视角） | 相机机位关系 | 正面平视 / 低角度仰视 / 微俯特写 |
| （基本站位/群像分布） | 多人物的空间排布 | 对称三角构图 / 前后错落叠压 / 环形包围 |
| （方位1/方位2） | 左右或前后定位 | 左侧 / 右后方 / 前景 |
| （姿态趋势） | 身体主轴走向 | 侧身微倾 / 单膝跪地 / 后仰反弓 |
| （局部动作） | 手/脚/头的动态 | 指尖轻触锁骨 / 脚尖点地 / 头部微偏 |
| （互动方式） | 角色间关系 | 依偎 / 拉扯 / 对视 / 环绕 |
| （肢体走向） | 视觉引导线 | 手臂延伸 / 腿部交错 / 发丝飘向 |
| （视觉重心） | 视线落点 | 画面中心 / 右上方负空间 / 交握的双手 |
| （环境类型） | 场景基底 | 纯白影棚 / 雨夜都市 / 幽暗森林 |
| （前景/中景元素） | 非主体装饰 | 飘落的花瓣 / 金属管道 / 雾气 |
| （空间关系） | 元素与主体距离 | 半透明悬浮 / 虚化背景衬托 / 前景遮挡 |
| （光源方向） | 主光来源 | 正前方柔光 / 侧逆光 / 顶光 |
| （明暗对比层次） | 光影强度 | 均匀漫射 / 高反差剪影 / 柔和过渡 |
| （艺术风格） | 绘画流派 | 日系赛璐璐 / 厚涂油画 / 3D渲染 |
| （线条特点） | 轮廓处理 | 干净利落 / 断续速写感 / 模糊晕染 |
| （主色调与点缀逻辑） | 色彩构成 | 低饱和冷灰调 / 高饱和暖色为主 |
| （光影渲染技法） | 质感生成方式 | 边缘光勾勒 / 体积光穿透 / 菲涅尔反射 |
| （整体氛围） | 情绪/叙事基调 | 宁静治愈 / 紧张对峙 / 慵懒暧昧 |

### 输出案例

**案例 1**: 三狐娘对称构图
```
three fox-eared anime girls with long flowing golden hair and large fluffy fox ears, central adult figure seated gracefully with crossed legs, flanked symmetrically by two younger versions of herself, all fully nude with smooth pale skin and subtle luminous highlights, central figure has amber eyes and a calm direct gaze, left girl leans inward with both hands gently resting on the center figure's chest, right girl stands slightly forward with one index finger lightly touching her lips, green eyes on both companions, long voluminous golden tails cascading behind, pure white background, faint semi-transparent rectangular panel floating behind the figures subtly revealing a close-up of the central character's eyes and hair strands, soft directional diffuse lighting casting gentle rim highlights, clean flowing linework with smooth cel shading, bright and transparent color palette, soft even gradients on skin, calm and healing atmosphere, masterpiece quality, highly detailed, 8k resolution, elegant vertical composition, delicate anatomical proportions, soft focus background edges, refined digital painting style, luminous skin texture, symmetrical posing, gentle expressions, airy fantasy aesthetic, polished rendering
```

**案例 2**: 双龙娘幻想
```
two ethereal dragon fairy hybrids, one larger crouching gracefully on the left, one smaller hovering dynamically on the right, large translucent moth-like wings with delicate vein patterns and glowing blue bioluminescent accents, pale skin traced with luminous cyan markings that follow natural muscle contours, dark hair flowing with subtle blue streaks and sharp geometric crown horns, piercing yellow eyes paired with dark lips, dark star-shaped chest armor plates, scaly serpentine lower bodies ending in pointed feet, elegant poised poses creating a staggered visual rhythm, soft atmospheric haze blending into a smooth gradient background from cool slate blue to warm pale beige, gentle directional lighting casting soft rim highlights on wing edges and skin, volumetric glow emanating from glowing seams and armor joints, semi-realistic fantasy digital painting style, clean flowing linework with rich textural contrast between translucent membranes and matte scaled skin, smooth shading with subtle subsurface scattering on pale tones, ethereal mystical atmosphere balanced by cinematic depth of field, masterpiece quality, highly detailed, 8k resolution, intricate anatomical design, delicate finger poses, serene confident expressions, dynamic composition leading the eye across the frame, cool and warm complementary color harmony, fine art concept illustration, polished rendering, elegant fantasy aesthetic, soft focus background elements, intricate wing segmentation, glowing blue accents on joints, graceful posture alignment, luminous skin texture, atmospheric perspective, refined digital brushwork, studio lighting simulation, premium illustration quality
```

## 使用场景

### 场景 1: 角色生图（纯 tag 模式）

```bash
python comfyui_draw.py \
  "masterpiece, best quality, newest, latest, safe, @wlop, 1girl, solo, silver hair, long hair, red eyes, white dress, standing, looking at viewer, castle background, moonlight, night sky" \
  --canvas 竖图 --steps 28 --cfg 5.5
```

### 场景 2: 高级描述（模板模式）

根据需要填充模板占位符，组装成英文段落。注意每段用逗号分隔，不要用句点。

**构建方法**:
1. 从占位符指南中选取合适的值
2. 翻译成英文并组装
3. 添加 `masterpiece, best quality` 结尾
4. 保持全小写，逗号分隔

### 场景 3: 画风切换

**常用画师标签**:
- `@wlop` - 唯美幻想风
- `@ask` - 精美日系
- `@fu_mi` - 性感厚涂
- `@big chungus` - 美式动画风

### 场景 4: 工作流配置

**工作流文件**: `anima-new-Latent.json`

**环境要求**:
- `COMFYUI_WORKFLOW_PATH=./anima-new-Latent.json`
- 必须从 skill 根目录运行
- 需要 `aiohttp` 包

**参数配置**:
```bash
python comfyui_draw.py "prompt" \
  --canvas 竖图 --steps 28 --cfg 5.5
```

## 注意事项

- ⚠️ Anima 不支持 SDXL LoRA
- ⚠️ 工作流必须从 skill 根目录运行
- ⚠️ 需要 aiohttp 包（`pip install aiohttp`）
- ⚠️ 模板段落中不要出现中文字符

更多警告见：[WARNINGS.md](../WARNINGS.md)

## 相关文档

- [Pretags Draw](../modules/pretags-draw/SKILL.md)
- [工作流节点映射](./workflow-node-mapping.md)
- [模型提示词对比](./model-prompt-comparison.md)

---

**最后更新**: 2026-06-09
