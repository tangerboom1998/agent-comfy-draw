# ComfyUI 常见陷阱与备用方案

> 合并自: host-url-pitfall.md, browser-api-direct-submission.md

---

## 一、Host URL 配置

### 问题

ComfyUI 连接失败，报 `ConnectionRefusedError` 或 `InvalidURL`。

### 根因

`COMFYUI_HOST` 环境变量**必须包含 `http://` 前缀**。缺少前缀时，`aiohttp` 无法解析为有效 URL。

### 错误表现

```
# ❌ 错误 — 缺少 http://
COMFYUI_HOST=192.168.1.100:8188
# → InvalidURL: 192.168.1.100:8188

# ❌ 错误 — 末尾斜杠
COMFYUI_HOST=http://192.168.1.100:8188/
# → 可能产生双斜杠 URL
```

### 正确配置

```bash
# ✅ 正确
COMFYUI_HOST=http://192.168.1.100:8188
```

---

## 二、浏览器 API 直接提交（备用方案）

### 适用场景

- 终端无法直接调用 Python 脚本
- Sandbox 环境缺少 Python 依赖
- 需要快速调试单个 workflow

### Step 1: 健康检查

在浏览器 Console（F12）中：

```javascript
(async () => {
    const r = await fetch('http://192.168.1.100:8188/system_stats');
    console.log(await r.json());
})();
```

### Step 2: 提交 Workflow

```javascript
(async () => {
    const workflow = { /* 你的 workflow JSON */ };
    workflow["27"]["inputs"]["text"] = "你的 prompt";
    workflow["3"]["inputs"]["seed"] = Math.floor(Math.random() * 1e14);
    
    const r = await fetch('http://192.168.1.100:8188/prompt', {
        method: 'POST',
        body: JSON.stringify({ prompt: workflow, client_id: "browser_console" })
    });
    const result = await r.json();
    console.log('Prompt ID:', result.prompt_id);
})();
```

### Step 3: 轮询结果

```javascript
(async () => {
    const promptId = 'YOUR_PROMPT_ID';
    while (true) {
        const r = await fetch(`http://192.168.1.100:8188/history/${promptId}`);
        const data = await r.json();
        if (data[promptId]) {
            console.log('完成!', data[promptId].outputs);
            break;
        }
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
})();
```

### Step 4: 定位输出文件 + 发送

```javascript
// 输出文件路径在 history 的 outputs 中
const outputs = data[promptId].outputs;
for (const [nodeId, nodeOutput] of Object.entries(outputs)) {
    if (nodeOutput.images) {
        for (const img of nodeOutput.images) {
            console.log(`ComfyUI URL: http://192.168.1.100:8188/view?filename=${img.filename}&subfolder=${img.subfolder || ''}&type=output`);
        }
    }
}
```

---

## 三、SDXL 工作流模板（非 z-image）

用于浏览器 Console 快速提交的简化版 SDXL 工作流 JSON 模板。

---

## 四、关键注意事项

### 1. browser_console 必须用 async IIFE

```javascript
// ✅ 正确
(async () => {
    // ... fetch ...
})();

// ❌ 错误（顶层 await 在旧浏览器不支持）
await fetch(...);
```

### 2. history 轮询首次返回空对象 `{}` 不代表失败

ComfyUI history API 在任务未完成时返回空对象。持续轮询直到 prompt_id 出现在响应中。

### 3. 输出文件路径不在 workspace 下

ComfyUI 的输出目录是 ComfyUI 自己的 `output/` 目录，不是项目 workspace 的 `output/`。

### 4. vision_analyze 对本地文件可能 404

如果 vision_analyze 无法访问 ComfyUI 的本地文件，使用 ComfyUI 的 `/view` URL。

### 5. 图片可通过 ComfyUI URL 直接分享（同网段）

```
http://192.168.1.100:8188/view?filename=CCUI_xxx_0.png&type=output
```
