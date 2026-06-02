"""ComfyUI 绘画工具 — nanobot Tool 集成（独立版）.

将 ComfyUI API 生图功能封装为 nanobot 可调用的 Tool。
自动集成 tag_producer 进行预设命令处理（人物/动作/画风/撸串/随机等）。
未匹配 pretags 的中文文本由 agent 后续调用 LLM 润色翻译。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# 确保 skill scripts 目录在 Python 路径中
_SCRIPTS_DIR = Path(__file__).resolve().parent
_SKILL_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from comfyui_client import CANVAS_PRESETS, SAMPLER_LIST, ComfyUIClient

# 尝试导入 tag_producer（同级 skill）
# tag_producer 依赖 pandas/numpy，沙箱环境可能间歇性缺失
# 若首次导入失败，尝试自动安装依赖后重试
try:
    from tag_producer import get_tag_producer as _get_tag_producer
    _HAS_TAG_PRODUCER = True
    _TAG_PRODUCER_ERROR = None
except ImportError as _e:
    import subprocess as _sp
    _TAG_PRODUCER_ERROR = str(_e)
    # 自动尝试安装缺失的依赖
    for _pkg in ['pandas', 'numpy']:
        if _pkg in _TAG_PRODUCER_ERROR.lower():
            _sp.run([sys.executable, '-m', 'pip', 'install', '-q', _pkg], timeout=30)
    try:
        from tag_producer import get_tag_producer as _get_tag_producer
        _HAS_TAG_PRODUCER = True
        _TAG_PRODUCER_ERROR = None
    except ImportError as _e2:
        _HAS_TAG_PRODUCER = False
        _TAG_PRODUCER_ERROR = str(_e2)


# ── nanobot Tool 基类兼容层 ──────────────────────────────────────────────
# 如果在 nanobot 环境中，使用 Tool 基类；否则提供独立运行模式

try:
    from nanobot.agent.tools.base import Tool, tool_parameters
    _IN_NANOBOT = True
except ImportError:
    _IN_NANOBOT = False

    # 提供 stub 类，使脚本可在非 nanobot 环境中独立运行
    class Tool:  # type: ignore[no-redef]
        pass

    def tool_parameters(schema):  # type: ignore[misc]
        def decorator(cls):
            cls._tool_schema = schema
            return cls
        return decorator


# ── 工具定义 ──────────────────────────────────────────────────────────────

_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": (
                "AI 绘画的正向提示词。"
                "支持中文关键词（会自动转换为英文 tag）和 <lora:LoraName:unet:clip> 格式的 LoRA 调用。"
            ),
        },
        "negative_prompt": {
            "type": "string",
            "description": "反向提示词，描述不希望出现的内容。留空使用默认反向提示词。",
        },
        "canvas": {
            "type": "string",
            "enum": list(CANVAS_PRESETS.keys()),
            "description": "画布预设：竖图(1024x1536)、横图(1536x1024)、方图(1280x1280)。默认竖图。",
        },
        "width": {
            "type": "integer",
            "description": "自定义宽度，优先级高于画布预设，上限 1920。-1 表示使用画布预设。",
            "minimum": -1,
            "maximum": 1920,
        },
        "height": {
            "type": "integer",
            "description": "自定义高度，优先级高于画布预设，上限 1920。-1 表示使用画布预设。",
            "minimum": -1,
            "maximum": 1920,
        },
        "steps": {
            "type": "integer",
            "description": "采样步数，默认 28，上限 50。步数越高质量越好但越慢。",
            "minimum": 1,
            "maximum": 50,
        },
        "sampler_index": {
            "type": "integer",
            "description": f"采样器索引。可选: {', '.join(f'{i}={s}' for i, s in enumerate(SAMPLER_LIST))}。默认 1(euler_ancestral)。",
            "minimum": 0,
            "maximum": len(SAMPLER_LIST) - 1,
        },
        "cfg": {
            "type": "number",
            "description": "CFG 自由度，控制提示词引导强度。默认 5.5，范围 1-30。",
            "minimum": 1.0,
            "maximum": 30.0,
        },
        "seed": {
            "type": "integer",
            "description": "随机种子。-1 为随机种子，指定种子可复现结果。",
            "minimum": -1,
        },
        "model_index": {
            "type": "integer",
            "description": "模型序号。1=tamix_ninini_v4, 2=noobaiXLNAIXL_epsilonPred11Version。默认 2。",
            "minimum": 1,
            "maximum": 10,
        },
        "upscale": {
            "type": "boolean",
            "description": "是否启用放大功能。默认 False。启用后使用 UltimateSDUpscale 和 4x-UltraSharp 模型进行放大。",
        },
        "upscale_by": {
            "type": "number",
            "description": "放大倍数，默认 1.3。范围 1.0-4.0。",
            "minimum": 1.0,
            "maximum": 4.0,
        },
        "upscale_steps": {
            "type": "integer",
            "description": "放大采样步数，默认 60。步数越高质量越好但越慢。",
            "minimum": 1,
            "maximum": 100,
        },
        "upscale_cfg": {
            "type": "number",
            "description": "放大 CFG 值，默认 7.5。范围 1-30。",
            "minimum": 1.0,
            "maximum": 30.0,
        },
        "upscale_sampler": {
            "type": "string",
            "description": "放大采样器，默认 euler_ancestral。",
        },
        "upscale_scheduler": {
            "type": "string",
            "description": "放大调度器，默认 karras。",
        },
        "upscale_denoise": {
            "type": "number",
            "description": "放大去噪强度，默认 0.25。范围 0-1。值越小越接近原图，值越大变化越大。",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "controlnet_image": {
            "type": "string",
            "description": "ControlNet 参考图本地路径。提供后启用 ControlNet 控制生成。",
        },
        "controlnet_strength": {
            "type": "number",
            "description": "ControlNet 控制强度，默认 0.8。范围 0-1。值越大越贴近参考图。",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "controlnet_type": {
            "type": "string",
            "enum": ["auto", "lineart", "anime_lineart", "canny", "depth", "pose", "scribble", "hed", "normal", "shuffle", "tile", "color", "manga", "none"],
            "description": "ControlNet 预处理类型。auto=自动选择线稿(最通用)。lineart=线稿, canny=边缘, depth=深度, pose=姿态, scribble=涂鸦, color=颜色, none=不预处理。",
        },
    },
    "required": ["prompt"],
}


@tool_parameters(_TOOL_SCHEMA)
class ComfyUIDrawTool(Tool):
    """AI 绘画工具：通过 ComfyUI API 生成图片。

    使用时需设置 COMFYUI_HOST 环境变量指向 ComfyUI 服务地址。
    生成完成后会通过 message 工具将图片发送给用户。
    """

    DEFAULT_NEGATIVE = (
        "lowres,(bad),text,error,fewer,extra,missing,worst quality,jpeg artifacts,"
        "low quality,watermark,unfinished,displeasing,oldest,faceless,"
        "bad background,NEGATIVE_HANDSXL,furry,extra arms,extra fingers,"
        "extra legs,extra toes,blush,"
    )

    DEFAULT_QUALITY_PREFIX = (
        "masterpiece, best quality, ultra-detailed, very aesthetic, absurdres, "
        "depth of field, best lighting"
    )

    def __init__(
        self,
        comfyui_host: str | None = None,
        workflow_path: str | None = None,
        output_dir: str | None = None,
        timeout: int = 300,
    ) -> None:
        """初始化 ComfyUI 绘画工具。

        Args:
            comfyui_host: ComfyUI 服务地址。
            workflow_path: 工作流模板路径。
            output_dir: 图片输出目录。
            timeout: 生图超时秒数。
        """
        host = comfyui_host or os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188")
        wf_path = workflow_path or os.environ.get("COMFYUI_WORKFLOW_PATH")
        out_dir = output_dir or os.environ.get("COMFYUI_OUTPUT_DIR", "output")
        self._client = ComfyUIClient(
            host=host,
            workflow_path=wf_path,
            output_dir=out_dir,
            timeout=timeout,
        )
        self._send_callback = None

    def set_send_callback(self, callback) -> None:
        """设置消息发送回调（由 AgentLoop 注入）。"""
        self._send_callback = callback

    @property
    def name(self) -> str:
        return "comfyui_draw"

    @property
    def description(self) -> str:
        return (
            "AI 绘画工具：根据提示词通过 ComfyUI 生成图片。"
            "支持中文提示词（自动翻译为英文 tag）、LoRA 调用、多种画布预设和采样器。"
            "生成完成后图片会自动发送给用户。"
        )

    @property
    def exclusive(self) -> bool:
        """绘画工具独占执行，避免并发导致 ComfyUI 过载。"""
        return True

    async def execute(self, **kwargs: Any) -> Any:
        """执行生图请求。"""
        prompt = kwargs.get("prompt", "")
        negative_prompt = kwargs.get("negative_prompt") or self.DEFAULT_NEGATIVE
        canvas = kwargs.get("canvas", "竖图")
        width = kwargs.get("width", -1)
        height = kwargs.get("height", -1)
        steps = kwargs.get("steps", 28)
        sampler_index = kwargs.get("sampler_index", 1)
        cfg = kwargs.get("cfg", 5.5)
        seed = kwargs.get("seed", -1)
        model_index = kwargs.get("model_index", 1)
        upscale = kwargs.get("upscale", False)
        upscale_by = kwargs.get("upscale_by", 1.3)
        upscale_steps = kwargs.get("upscale_steps", 60)
        upscale_cfg = kwargs.get("upscale_cfg", 7.5)
        upscale_sampler = kwargs.get("upscale_sampler", "euler_ancestral")
        upscale_scheduler = kwargs.get("upscale_scheduler", "karras")
        upscale_denoise = kwargs.get("upscale_denoise", 0.25)
        controlnet_image = kwargs.get("controlnet_image", "")
        controlnet_strength = kwargs.get("controlnet_strength", 0.8)
        controlnet_type = kwargs.get("controlnet_type", "auto")

        if not prompt.strip():
            return "错误：提示词不能为空"

        try:
            print(f"ComfyUI 生图开始: prompt={prompt[:100]}...")

            # 先通过 tag_producer 处理提示词
            processed_prompt = await self._process_prompt(prompt)

            # 自动注入质量前缀（如果提示词中尚未包含）
            if not any(kw in processed_prompt[:30].lower() for kw in ["masterpiece", "best quality"]):
                processed_prompt = f"{self.DEFAULT_QUALITY_PREFIX}, {processed_prompt}"
                print(f"✓ 质量前缀已注入")

            image_paths = await self._client.generate(
                prompt=processed_prompt,
                negative_prompt=negative_prompt,
                canvas=canvas,
                width=width,
                height=height,
                steps=steps,
                sampler_index=sampler_index,
                cfg=cfg,
                seed=seed,
                model_index=model_index,
                upscale=upscale,
                upscale_by=upscale_by,
                upscale_steps=upscale_steps,
                upscale_cfg=upscale_cfg,
                upscale_sampler=upscale_sampler,
                upscale_scheduler=upscale_scheduler,
                upscale_denoise=upscale_denoise,
                controlnet_image=controlnet_image,
                controlnet_strength=controlnet_strength,
                controlnet_type=controlnet_type,
            )

            if not image_paths:
                return "生图完成但未获得图片"

            result_lines = [
                f"✅ 生图完成！共生成 {len(image_paths)} 张图片",
                f"提示词: {processed_prompt[:200]}{'...' if len(processed_prompt) > 200 else ''}",
                f"参数: {canvas}, {steps}步, CFG={cfg}, 种子={seed}",
            ]

            if upscale:
                result_lines.append(f"放大: {upscale_by}x, 步数={upscale_steps}, 去噪={upscale_denoise}")

            # 如果有消息发送回调，发送图片
            if self._send_callback:
                try:
                    from nanobot.bus.events import OutboundMessage
                    for img_path in image_paths:
                        try:
                            msg = OutboundMessage(
                                channel="",
                                chat_id="",
                                content="",
                                media=[str(img_path)],
                            )
                            await self._send_callback(msg)
                        except Exception as e:
                            print(f"⚠ 发送图片消息失败: {e}")
                except ImportError:
                    pass

            paths_str = "\n".join(f"  - {p}" for p in image_paths)
            result_lines.append(f"图片路径:\n{paths_str}")

            return "\n".join(result_lines)

        except TimeoutError:
            return "❌ 生图超时，ComfyUI 可能繁忙，请稍后重试"
        except ConnectionError:
            return "❌ 无法连接 ComfyUI 服务，请检查服务是否运行"
        except Exception as e:
            return f"❌ 生图失败: {str(e)}"

    async def _process_prompt(self, prompt: str) -> str:
        """通过 tag_producer 处理预设命令。

        只处理 pretags.json 中的预设命令（人物/动作/画风/撸串/随机等）。
        未匹配 pretags 的中文文本原样保留，由 agent 后续调用 LLM 润色翻译。
        """
        if not _HAS_TAG_PRODUCER:
            print(f"tag_producer 不可用: {_TAG_PRODUCER_ERROR}, 使用原始提示词")
            return prompt
        try:
            tp = _get_tag_producer()
            processed = tp.tagrep(prompt)
            print(f"tag_producer: '{prompt[:50]}' → '{processed[:50]}'")
            return processed
        except Exception as e:
            print(f"tag_producer 处理失败: {e}, 使用原始提示词")
            return prompt


# ── 独立运行入口 ──────────────────────────────────────────────────────────

async def _main():
    """独立测试入口。"""
    import argparse
    import io
    # Windows GBK 兼容：强制 stdout 使用 UTF-8
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="ComfyUI Draw 独立测试")
    parser.add_argument("prompt", help="提示词")
    parser.add_argument("--host", default=None, help="ComfyUI 地址")
    parser.add_argument("--canvas", default="竖图", choices=list(CANVAS_PRESETS.keys()))
    parser.add_argument("--steps", type=int, default=28)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("--cfg", type=float, default=5.5, help="CFG 值 (默认 5.5)")
    parser.add_argument("--model", type=int, default=1, help="模型序号 (默认 1=tamix_ninini_v4)")
    parser.add_argument("--negative", default="", help="负面提示词")
    # 放大参数
    parser.add_argument("--upscale", action="store_true", help="启用放大功能")
    parser.add_argument("--upscale-by", type=float, default=1.3, help="放大倍数 (默认 1.3)")
    parser.add_argument("--upscale-steps", type=int, default=60, help="放大采样步数 (默认 60)")
    parser.add_argument("--upscale-cfg", type=float, default=7.5, help="放大 CFG 值 (默认 7.5)")
    parser.add_argument("--upscale-sampler", default="euler_ancestral", help="放大采样器 (默认 euler_ancestral)")
    parser.add_argument("--upscale-scheduler", default="karras", help="放大调度器 (默认 karras)")
    parser.add_argument("--upscale-denoise", type=float, default=0.25, help="放大去噪强度 (默认 0.25)")
    # ControlNet 参数
    parser.add_argument("--controlnet-image", default="", help="ControlNet 参考图本地路径")
    parser.add_argument("--controlnet-strength", type=float, default=0.8, help="ControlNet 强度 (默认 0.8)")
    parser.add_argument("--controlnet-type", default="auto",
                        choices=["auto", "lineart", "anime_lineart", "canny", "depth", "pose", "scribble", "hed", "normal", "shuffle", "tile", "color", "manga", "none"],
                        help="ControlNet 预处理类型 (默认 auto=线稿)")
    args = parser.parse_args()

    tool = ComfyUIDrawTool(comfyui_host=args.host)
    result = await tool.execute(
        prompt=args.prompt,
        negative_prompt=args.negative,
        canvas=args.canvas,
        steps=args.steps,
        seed=args.seed,
        cfg=args.cfg,
        model_index=args.model,
        upscale=args.upscale,
        upscale_by=args.upscale_by,
        upscale_steps=args.upscale_steps,
        upscale_cfg=args.upscale_cfg,
        upscale_sampler=args.upscale_sampler,
        upscale_scheduler=args.upscale_scheduler,
        upscale_denoise=args.upscale_denoise,
        controlnet_image=args.controlnet_image,
        controlnet_strength=args.controlnet_strength,
        controlnet_type=args.controlnet_type,
    )
    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(_main())
