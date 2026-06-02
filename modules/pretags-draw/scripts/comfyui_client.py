"""ComfyUI API 客户端模块 — 独立版.

通过 HTTP API 与 ComfyUI 交互，提交工作流、轮询进度、获取生成结果。
"""

from __future__ import annotations

import asyncio
import json
import random
import uuid
from pathlib import Path
from typing import Any

import aiohttp

# ── 数据文件路径 ──────────────────────────────────────────────────────────
_SKILL_ROOT = Path(__file__).resolve().parent.parent  # skill 根目录
_ASSETS_DIR = _SKILL_ROOT / "assets"

DEFAULT_WORKFLOW_PATH = str(_ASSETS_DIR / "noob_api_fix_upscale_face_detailer.json")


# ── 采样器映射表 ──────────────────────────────────────────────────────────
SAMPLER_LIST: list[str] = [
    "euler",
    "euler_ancestral",
    "heun",
    "heunpp2",
    "dpm_2",
    "dpm_2_ancestral",
    "lms",
    "dpmpp_2s_ancestral",
    "dpmpp_sde",
    "dpmpp_2m",
    "dpmpp_2m_sde",
    "dpmpp_3m_sde",
    "ddpm",
    "lcm",
    "ddim",
    "uni_pc",
    "uni_pc_bh2",
]

# ── 画布预设 ──────────────────────────────────────────────────────────────
CANVAS_PRESETS: dict[str, tuple[int, int]] = {
    "竖图": (1024, 1536),
    "横图": (1536, 1024),
    "方图": (1280, 1280),
}

# ── 模型切换映射 (node 88 Input 值) ──────────────────────────────────────
MODEL_SWITCH_MAP: dict[int, int] = {
    1: 1,   # tamix_ninini_v4
    2: 2,   # noobaiXLNAIXL_epsilonPred11Version
    10: 1,  # 默认使用 tamix_ninini_v4
}


class ComfyUIClient:
    """异步 ComfyUI API 客户端.

    Parameters
    ----------
    host : str
        ComfyUI 服务地址，例如 ``http://127.0.0.1:8188``
    workflow_path : str | Path
        工作流 JSON 模板路径
    output_dir : str | Path
        生成图片的输出目录
    timeout : int
        生成超时时间（秒）
    """

    def __init__(
        self,
        host: str = "http://127.0.0.1:8188",
        workflow_path: str | Path | None = None,
        output_dir: str | Path = "output",
        timeout: int = 300,
    ) -> None:
        self.host = host.rstrip("/")
        self.workflow_path = Path(workflow_path) if workflow_path else Path(DEFAULT_WORKFLOW_PATH)
        self.output_dir = Path(output_dir)
        self.timeout = timeout
        self._workflow_template: dict[str, Any] | None = None

    # ── 工作流模板加载 ────────────────────────────────────────────────────

    def _load_workflow(self) -> dict[str, Any]:
        """加载并缓存工作流模板。"""
        if self._workflow_template is None:
            with open(self.workflow_path, encoding="utf-8") as f:
                self._workflow_template = json.load(f)
        return json.loads(json.dumps(self._workflow_template))  # deep copy

    def _detect_workflow_type(self) -> str:
        """根据工作流文件名检测类型: noob / anima / zimage"""
        name = self.workflow_path.name.lower()
        if 'anima' in name:
            return 'anima'
        if 'z_image' in name or 'zturbo' in name:
            return 'zimage'
        return 'noob'

    def _build_workflow_anima(
        self,
        wf: dict[str, Any],
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        sampler_name: str,
        cfg: float,
        seed: int,
        filename_prefix: str,
        upscale: bool = False,
        upscale_scale: float = 1.25,
        upscale_steps: int = 15,
        upscale_cfg: float = 6,
        upscale_denoise: float = 0.3,
        upscale_sampler: str = "euler",
        upscale_scheduler: str = "beta",
    ) -> dict[str, Any]:
        """构建 Anima 工作流（anima-new-Latent.json）"""
        # 注入提示词 (node 10)
        wf["10"]["inputs"]["input"] = prompt

        # 反向提示词 (node 37)
        wf["37"]["inputs"]["text"] = negative_prompt

        # 宽高 (node 2, 3)
        wf["2"]["inputs"]["int"] = width
        wf["3"]["inputs"]["int"] = height

        # 主采样 (node 30)
        wf["30"]["inputs"]["steps"] = steps
        wf["30"]["inputs"]["sampler_name"] = sampler_name
        wf["30"]["inputs"]["cfg"] = cfg

        # 种子 (node 4)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        wf["4"]["inputs"]["seed"] = seed

        if upscale:
            # 放大管线：CR Upscale Image[69] + VAEEncode[71] + KSampler[73] + VAEDecode[72] + FaceDetailer[75]
            # Node 69: CR Upscale Image — 4x-UltraSharp 模型放大
            wf["69"]["inputs"]["upscale_model"] = "4x-UltraSharp.pth"
            wf["69"]["inputs"]["rescale_factor"] = upscale_scale
            wf["69"]["inputs"]["mode"] = "rescale"
            wf["69"]["inputs"]["resampling_method"] = "lanczos"
            
            # Node 73: 二次采样 (img2img)
            upscale_seed = random.randint(0, 2**32 - 1)
            wf["73"]["inputs"]["seed"] = upscale_seed
            wf["73"]["inputs"]["steps"] = upscale_steps
            wf["73"]["inputs"]["cfg"] = upscale_cfg
            wf["73"]["inputs"]["denoise"] = upscale_denoise
            wf["73"]["inputs"]["sampler_name"] = upscale_sampler
            wf["73"]["inputs"]["scheduler"] = upscale_scheduler
            
            # Node 75: 面部修复种子
            wf["75"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)
            
            # Node 76: 放大保存
            wf["76"]["inputs"]["filename_prefix"] = f"{filename_prefix}_up"
            
            print(f"✓ Anima 放大已启用: 模型=4x-UltraSharp, 倍率={upscale_scale}x, "
                  f"二次采样={upscale_steps}步, CFG={upscale_cfg}, denoise={upscale_denoise}")
        else:
            # 移除放大路径节点 (67,69,71,72,73,75,76)
            for nid in ["67", "69", "71", "72", "73", "75", "76"]:
                if nid in wf:
                    del wf[nid]

        return wf

    def _build_workflow_zimage(
        self,
        wf: dict[str, Any],
        prompt: str,
        negative_prompt: str,
        steps: int,
        seed: int,
        filename_prefix: str,
        upscale: bool = False,
        upscale_scale: float = 1.25,
        upscale_steps: int = 10,
        upscale_cfg: float = 1,
        upscale_denoise: float = 0.5,
        upscale_sampler: str = "euler",
        upscale_scheduler: str = "beta",
    ) -> dict[str, Any]:
        """构建 z-image turbo 工作流（z_image_turbo_new.json）"""
        # 注入提示词 (node 31 — FETextInput)
        wf["31"]["inputs"]["input"] = prompt

        # 反向提示词 (node 7)
        wf["7"]["inputs"]["text"] = negative_prompt

        # 主采样 (node 3)
        wf["3"]["inputs"]["steps"] = steps
        wf["3"]["inputs"]["cfg"] = 1  # z-image turbo 固定 cfg=1

        # 种子 (node 51)
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        wf["51"]["inputs"]["seed"] = seed

        if upscale:
            # 保留放大路径节点 (45-50)
            wf["47"]["inputs"]["scale_by"] = upscale_scale  # LatentUpscaleBy
            
            wf["45"]["inputs"]["steps"] = upscale_steps
            wf["45"]["inputs"]["cfg"] = upscale_cfg
            wf["45"]["inputs"]["denoise"] = upscale_denoise
            wf["45"]["inputs"]["sampler_name"] = upscale_sampler
            wf["45"]["inputs"]["scheduler"] = upscale_scheduler
            
            # 放大后面部修复 (node 48)
            wf["48"]["inputs"]["steps"] = 10
            wf["48"]["inputs"]["seed"] = [wf["51"]["inputs"]["seed"], 0]
            
            # 放大保存节点 (node 50)
            wf["50"]["inputs"]["filename_prefix"] = f"{filename_prefix}_up"
            
            print(f"✓ z-image 放大已启用: 倍率={upscale_scale}x, 步数={upscale_steps}, "
                  f"CFG={upscale_cfg}, denoise={upscale_denoise}")
        else:
            # 移除放大路径节点
            for nid in ["45", "46", "47", "48", "49", "50"]:
                if nid in wf:
                    del wf[nid]

        return wf

    def _build_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        sampler_name: str,
        cfg: float,
        seed: int,
        model_index: int,
        filename_prefix: str,
        upscale: bool = False,
        upscale_by: float = 1.3,
        upscale_steps: int = 60,
        upscale_cfg: float = 7.5,
        upscale_sampler: str = "euler_ancestral",
        upscale_scheduler: str = "karras",
        upscale_denoise: float = 0.25,
    ) -> dict[str, Any]:
        """根据参数构建 ComfyUI 工作流。"""
        wf = self._load_workflow()
        wf_type = self._detect_workflow_type()

        # ── 按工作流类型分发 ──
        if wf_type == 'anima':
            return self._build_workflow_anima(
                wf, prompt, negative_prompt, width, height,
                steps, sampler_name, cfg, seed, filename_prefix,
                upscale=upscale,
                upscale_scale=min(upscale_by, 2.0),
                upscale_steps=upscale_steps,
                upscale_cfg=upscale_cfg,
                upscale_denoise=upscale_denoise,
                upscale_sampler=upscale_sampler,
                upscale_scheduler=upscale_scheduler,
            )

        if wf_type == 'zimage':
            return self._build_workflow_zimage(
                wf, prompt, negative_prompt,
                steps, seed, filename_prefix,
                upscale=upscale,
                upscale_scale=min(upscale_by, 2.0),
                upscale_steps=upscale_steps,
                upscale_cfg=upscale_cfg,
                upscale_denoise=upscale_denoise,
                upscale_sampler=upscale_sampler,
                upscale_scheduler=upscale_scheduler,
            )

        # ── Noob 工作流（原逻辑） ──
        wf["85"]["inputs"]["input"] = prompt
        wf["14"]["inputs"]["text"] = negative_prompt
        wf["20"]["inputs"]["int"] = width
        wf["21"]["inputs"]["int"] = height
        wf["48"]["inputs"]["steps"] = steps
        wf["48"]["inputs"]["sampler_name"] = sampler_name
        wf["48"]["inputs"]["cfg"] = cfg
        if seed == -1:
            seed = random.randint(0, 2**32 - 1)
        wf["32"]["inputs"]["seed"] = seed
        switch_val = MODEL_SWITCH_MAP.get(model_index, 2)
        wf["88"]["inputs"]["Input"] = switch_val
        wf["83"]["inputs"]["filename_prefix"] = filename_prefix

        if upscale:
            required_upscale_nodes = ["94", "95", "96", "97"]
            missing_upscale = [n for n in required_upscale_nodes if n not in wf]
            if missing_upscale:
                print(f"⚠ 当前工作流不支持放大功能（缺少节点: {', '.join(missing_upscale)}），跳过放大")
            else:
                upscale_seed = random.randint(0, 2**32 - 1)
                wf["94"]["inputs"]["upscale_by"] = upscale_by
                wf["94"]["inputs"]["seed"] = upscale_seed
                wf["94"]["inputs"]["steps"] = upscale_steps
                wf["94"]["inputs"]["cfg"] = upscale_cfg
                wf["94"]["inputs"]["sampler_name"] = upscale_sampler
                wf["94"]["inputs"]["scheduler"] = upscale_scheduler
                wf["94"]["inputs"]["denoise"] = upscale_denoise
                wf["96"]["inputs"]["filename_prefix"] = f"{filename_prefix}_upscaled"
                print(f"✓ Noob 放大功能已启用: 放大倍数={upscale_by}, 步数={upscale_steps}, 去噪={upscale_denoise}")
        else:
            for node_id in ["94", "95", "96", "97"]:
                if node_id in wf:
                    del wf[node_id]

        return wf

    # ── API 交互 ──────────────────────────────────────────────────────────

    async def _queue_prompt(
        self,
        session: aiohttp.ClientSession,
        workflow: dict[str, Any],
    ) -> str:
        """提交工作流到 ComfyUI 队列，返回 prompt_id。"""
        payload = {"prompt": workflow}
        async with session.post(f"{self.host}/prompt", json=payload) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"ComfyUI prompt 提交失败 (HTTP {resp.status}): {text}")
            data = await resp.json()
            prompt_id: str = data["prompt_id"]
            print(f"ComfyUI prompt 已提交: {prompt_id}")
            return prompt_id

    async def _wait_for_completion(
        self,
        session: aiohttp.ClientSession,
        prompt_id: str,
    ) -> dict[str, Any]:
        """轮询 ComfyUI 历史记录，等待生成完成。"""
        elapsed = 0.0
        poll_interval = 2.0
        while elapsed < self.timeout:
            async with session.get(f"{self.host}/history/{prompt_id}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if prompt_id in data:
                        history = data[prompt_id]
                        if "status" in history:
                            status = history["status"]
                            if status.get("status_str") == "error":
                                raise RuntimeError(
                                    f"ComfyUI 生成失败: {status.get('messages', '未知错误')}"
                                )
                        outputs = history.get("outputs", {})
                        if outputs:
                            return history
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            if int(elapsed) % 10 == 0:
                print(f"ComfyUI 生成中... 已等待 {int(elapsed)}s")

        raise TimeoutError(f"ComfyUI 生成超时 ({self.timeout}s), prompt_id={prompt_id}")

    def _extract_output_images(self, history: dict[str, Any]) -> list[dict[str, str]]:
        """从历史记录中提取输出图片信息。"""
        images: list[dict[str, str]] = []
        for node_id, node_output in history.get("outputs", {}).items():
            for img in node_output.get("images", []):
                images.append(img)
        return images

    async def _download_image(
        self,
        session: aiohttp.ClientSession,
        image_info: dict[str, str],
        save_path: Path,
    ) -> Path:
        """从 ComfyUI 下载单张图片到本地。"""
        params = {
            "filename": image_info["filename"],
            "subfolder": image_info.get("subfolder", ""),
            "type": image_info.get("type", "output"),
        }
        async with session.get(f"{self.host}/view", params=params) as resp:
            if resp.status != 200:
                raise RuntimeError(f"下载图片失败: {image_info['filename']}")
            save_path.parent.mkdir(parents=True, exist_ok=True)
            content = await resp.read()
            save_path.write_bytes(content)
            print(f"图片已保存: {save_path}")
            return save_path

    # ── 图片上传（ControlNet 参考图） ───────────────────────────────────────

    async def _upload_image(
        self,
        session: aiohttp.ClientSession,
        image_path: str | Path,
    ) -> str:
        """上传本地图片到 ComfyUI，返回服务端文件名。"""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"ControlNet 参考图不存在: {image_path}")

        form = aiohttp.FormData()
        form.add_field("image", open(image_path, "rb"), filename=image_path.name)
        form.add_field("overwrite", "true")

        async with session.post(f"{self.host}/upload/image", data=form) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"图片上传失败 (HTTP {resp.status}): {text}")
            data = await resp.json()
            filename = data.get("name", image_path.name)
            print(f"ControlNet 参考图已上传: {filename}")
            return filename

    # ── ControlNet 工作流注入 ───────────────────────────────────────────────

    def _inject_controlnet(
        self,
        wf: dict[str, Any],
        uploaded_filename: str,
        strength: float = 0.8,
        preprocessor: str = "LineArtPreprocessor",
        cn_model: str = "controlnet_union_sdxl_for_all_job_lineart.safetensors",
    ) -> dict[str, Any]:
        """向工作流注入 ControlNet 节点。"""
        # Node 200: LoadImage — 加载上传的参考图
        wf["200"] = {
            "class_type": "LoadImage",
            "inputs": {"image": uploaded_filename},
        }

        # Node 201: AIO_Preprocessor — 预处理参考图
        wf["201"] = {
            "class_type": "AIO_Preprocessor",
            "inputs": {
                "image": ["200", 0],
                "preprocessor": preprocessor,
                "resolution": 1024,
            },
        }

        # Node 202: ControlNetLoader — 加载 ControlNet 模型
        wf["202"] = {
            "class_type": "ControlNetLoader",
            "inputs": {"control_net_name": cn_model},
        }

        # Node 203: ControlNetApplyAdvanced — 应用 ControlNet
        # 读取原 CLIP 编码器(node 10)的 positive conditioning，注入 ControlNet
        wf["203"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["10", 0],          # 原 positive conditioning
                "negative": ["14", 0],          # 原 negative conditioning
                "control_net": ["202", 0],      # ControlNet 模型
                "image": ["201", 0],            # 预处理后的图片
                "strength": strength,
                "start_percent": 0.0,
                "end_percent": 0.9,
            },
        }

        # 将 KSampler(node 48) 的 positive 输入从 node 10 改为 node 203
        wf["48"]["inputs"]["positive"] = ["203", 0]

        print(f"✓ ControlNet 已注入: preprocessor={preprocessor}, strength={strength}")
        return wf

    @staticmethod
    def _resolve_controlnet_type(cn_type: str) -> str:
        """将用户友好的 controlnet_type 映射到 AIO_Preprocessor 预处理器名。"""
        TYPE_MAP = {
            "auto": "LineArtPreprocessor",          # 自动 → 线稿（最通用）
            "lineart": "LineArtPreprocessor",        # 线稿
            "anime_lineart": "AnimeLineArtPreprocessor",  # 动漫线稿
            "canny": "CannyEdgePreprocessor",        # Canny 边缘
            "depth": "DepthAnythingV2Preprocessor",  # 深度图
            "pose": "OpenposePreprocessor",          # 姿态
            "scribble": "ScribblePreprocessor",      # 涂鸦
            "hed": "HEDPreprocessor",                # HED 边缘
            "normal": "BAE-NormalMapPreprocessor",   # 法线图
            "shuffle": "ShufflePreprocessor",        # 内容重排
            "tile": "TilePreprocessor",              # 瓦片
            "color": "ColorPreprocessor",            # 颜色
            "manga": "Manga2Anime_LineArt_Preprocessor",  # 漫画转动漫线稿
            "none": "none",                          # 不预处理
        }
        return TYPE_MAP.get(cn_type.lower(), "LineArtPreprocessor")

    # ── 公开接口 ──────────────────────────────────────────────────────────

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        canvas: str = "竖图",
        width: int = -1,
        height: int = -1,
        steps: int = 28,
        sampler_index: int = 2,
        cfg: float = 7.0,
        seed: int = -1,
        model_index: int = 10,
        upscale: bool = False,
        upscale_by: float = 1.3,
        upscale_steps: int = 60,
        upscale_cfg: float = 7.5,
        upscale_sampler: str = "euler_ancestral",
        upscale_scheduler: str = "karras",
        upscale_denoise: float = 0.25,
        controlnet_image: str = "",
        controlnet_strength: float = 0.8,
        controlnet_type: str = "auto",
    ) -> list[Path]:
        """提交生图请求并等待结果。

        Parameters
        ----------
        upscale : bool
            是否启用放大功能
        upscale_by : float
            放大倍数，默认 1.3
        upscale_steps : int
            放大采样步数，默认 60
        upscale_cfg : float
            放大 CFG 值，默认 7.5
        upscale_sampler : str
            放大采样器，默认 euler_ancestral
        upscale_scheduler : str
            放大调度器，默认 karras
        upscale_denoise : float
            放大去噪强度，默认 0.25

        Returns
        -------
        list[Path]
            生成图片的本地路径列表
        """
        if canvas in CANVAS_PRESETS:
            default_w, default_h = CANVAS_PRESETS[canvas]
        else:
            default_w, default_h = CANVAS_PRESETS["竖图"]

        final_w = min(width, 1920) if width != -1 else default_w
        final_h = min(height, 1920) if height != -1 else default_h
        final_steps = min(steps, 50)

        if 0 <= sampler_index < len(SAMPLER_LIST):
            sampler_name = SAMPLER_LIST[sampler_index]
        else:
            sampler_name = SAMPLER_LIST[1]

        filename_prefix = f"CCUI_{uuid.uuid4().hex[:10]}"

        workflow = self._build_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=final_w,
            height=final_h,
            steps=final_steps,
            sampler_name=sampler_name,
            cfg=cfg,
            seed=seed,
            model_index=model_index,
            filename_prefix=filename_prefix,
            upscale=upscale,
            upscale_by=upscale_by,
            upscale_steps=upscale_steps,
            upscale_cfg=upscale_cfg,
            upscale_sampler=upscale_sampler,
            upscale_scheduler=upscale_scheduler,
            upscale_denoise=upscale_denoise,
        )

        async with aiohttp.ClientSession() as session:
            # ControlNet: 上传参考图并注入节点
            if controlnet_image:
                uploaded_name = await self._upload_image(session, controlnet_image)
                preprocessor = self._resolve_controlnet_type(controlnet_type)
                workflow = self._inject_controlnet(
                    workflow,
                    uploaded_filename=uploaded_name,
                    strength=controlnet_strength,
                    preprocessor=preprocessor,
                )
                # ControlNet 专用默认参数：steps=38, cfg=5.5
                if steps == 28:  # 用户未自定义 steps 时
                    workflow["48"]["inputs"]["steps"] = 38
                if cfg == 7.0:   # 用户未自定义 cfg 时
                    workflow["48"]["inputs"]["cfg"] = 5.5
                print(f"✓ ControlNet 参数: steps={workflow['48']['inputs']['steps']}, cfg={workflow['48']['inputs']['cfg']}")

            prompt_id = await self._queue_prompt(session, workflow)
            history = await self._wait_for_completion(session, prompt_id)
            image_infos = self._extract_output_images(history)

            if not image_infos:
                raise RuntimeError("ComfyUI 生成完成但未返回图片")

            saved_paths: list[Path] = []
            for img_info in image_infos:
                ext = Path(img_info["filename"]).suffix or ".png"
                save_name = f"{filename_prefix}_{len(saved_paths)}{ext}"
                save_path = self.output_dir / save_name
                await self._download_image(session, img_info, save_path)
                saved_paths.append(save_path)

        return saved_paths

    async def get_model_list(self) -> list[dict[str, Any]]:
        """从 ComfyUI API 获取可用模型列表。"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.host}/object_info/CheckpointLoaderSimple") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    models = (
                        data.get("CheckpointLoaderSimple", {})
                        .get("input", {})
                        .get("required", {})
                        .get("ckpt_name", [[]])
                    )
                    if models:
                        return [{"index": i, "name": m} for i, m in enumerate(models[0])]
                return []

    async def get_queue_status(self) -> dict[str, Any]:
        """获取 ComfyUI 队列状态。"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.host}/queue") as resp:
                if resp.status == 200:
                    return await resp.json()
                return {}
