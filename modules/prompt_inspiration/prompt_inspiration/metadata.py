"""Extract prompt metadata from AI-generated images.

Supports:
- ComfyUI: stores full workflow JSON in PNG tEXt 'prompt' chunk
- Stable Diffusion WebUI / Forge: stores generation params in PNG tEXt 'parameters' chunk
- A1111 PNG Info: stores in 'parameters' or 'postprocessing' chunks
"""

import json
import logging
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ImageMetadata:
    """Structured result from image metadata extraction."""
    source: str  # "comfyui", "webui", or "unknown"
    positive_prompt: str = ""
    negative_prompt: str = ""
    positive_prompts: List[str] = field(default_factory=list)
    negative_prompts: List[str] = field(default_factory=list)
    sampler: str = ""
    steps: int = 0
    cfg: float = 0.0
    seed: int = -1
    scheduler: str = ""
    denoise: float = 0.0
    model: str = ""
    model_hash: str = ""
    loras: List[str] = field(default_factory=list)
    size: str = ""
    raw_params: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def has_prompt(self) -> bool:
        return bool(self.positive_prompt or self.positive_prompts)

    def best_positive(self) -> str:
        """Return the longest positive prompt (most descriptive)."""
        candidates = self.positive_prompts or ([self.positive_prompt] if self.positive_prompt else [])
        if not candidates:
            return ""
        return max(candidates, key=len)

    def best_negative(self) -> str:
        candidates = self.negative_prompts or ([self.negative_prompt] if self.negative_prompt else [])
        if not candidates:
            return ""
        return max(candidates, key=len)

    def summary(self) -> str:
        """Human-readable summary of extracted metadata."""
        parts = [f"Source: {self.source}"]
        if self.model:
            parts.append(f"Model: {self.model}")
        if self.positive_prompt or self.positive_prompts:
            best = self.best_positive()
            if len(best) > 200:
                best = best[:200] + "..."
            parts.append(f"Positive: {best}")
        if self.negative_prompt or self.negative_prompts:
            best = self.best_negative()
            if len(best) > 100:
                best = best[:100] + "..."
            parts.append(f"Negative: {best}")
        if self.loras:
            parts.append(f"LoRA: {', '.join(self.loras)}")
        if self.sampler:
            params = f"Sampler: {self.sampler}"
            if self.steps:
                params += f", Steps: {self.steps}"
            if self.cfg:
                params += f", CFG: {self.cfg}"
            if self.seed >= 0:
                params += f", Seed: {self.seed}"
            parts.append(params)
        return "\n".join(parts)


def _read_png_text_chunks(filepath: str) -> dict[str, str]:
    """Read all tEXt, iTXt, zTXt chunks from a PNG file."""
    results: dict[str, str] = {}
    try:
        with open(filepath, "rb") as f:
            sig = f.read(8)
            if sig != b"\x89PNG\r\n\x1a\n":
                return results
            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                length = struct.unpack(">I", header[:4])[0]
                chunk_type = header[4:8].decode("ascii", errors="replace")
                data = f.read(length)
                crc = f.read(4)  # noqa: F841

                if chunk_type == "tEXt":
                    parts = data.split(b"\x00", 1)
                    key = parts[0].decode("latin-1")
                    val = parts[1].decode("latin-1", errors="replace") if len(parts) > 1 else ""
                    results[key] = val

                elif chunk_type == "zTXt":
                    parts = data.split(b"\x00", 1)
                    key = parts[0].decode("latin-1")
                    comp_data = parts[1] if len(parts) > 1 else b""
                    if comp_data and comp_data[0] == 0:
                        try:
                            val = zlib.decompress(comp_data[1:]).decode("latin-1", errors="replace")
                            results[key] = val
                        except zlib.error:
                            pass

                elif chunk_type == "iTXt":
                    parts = data.split(b"\x00", 5)
                    key = parts[0].decode("latin-1")
                    compressed = data[len(parts[0]) + 1] if len(data) > len(parts[0]) + 1 else 0
                    val_raw = parts[5] if len(parts) > 5 else b""
                    if compressed:
                        try:
                            val_raw = zlib.decompress(val_raw)
                        except zlib.error:
                            pass
                    try:
                        results[key] = val_raw.decode("utf-8")
                    except UnicodeDecodeError:
                        results[key] = val_raw.decode("latin-1", errors="replace")
    except Exception as e:
        logger.debug("Failed to read PNG metadata from %s: %s", filepath, e)
    return results


def _read_jpeg_exif(filepath: str) -> dict[str, str]:
    """Read EXIF/UserComment from JPEG (WebUI also saves params there)."""
    results: dict[str, str] = {}
    try:
        with open(filepath, "rb") as f:
            sig = f.read(2)
            if sig != b"\xff\xd8":
                return results
            while True:
                marker = f.read(2)
                if len(marker) < 2:
                    break
                if marker[0] != 0xFF:
                    break
                if marker[1] == 0xD9:
                    break
                if marker[1] in (0xDA,):
                    break
                size_bytes = f.read(2)
                if len(size_bytes) < 2:
                    break
                size = struct.unpack(">H", size_bytes)[0]
                payload = f.read(size - 2)
                if marker[1] == 0xE1:
                    text = payload.decode("latin-1", errors="replace")
                    if "parameters" in text[:20].lower():
                        idx = text.find("parameters")
                        if idx >= 0:
                            val = text[idx:].split("\x00", 1)[-1].strip()
                            if val:
                                results["parameters"] = val
    except Exception as e:
        logger.debug("Failed to read JPEG metadata from %s: %s", filepath, e)
    return results


def _parse_lora_strings(text: str) -> List[str]:
    """Extract LoRA references from prompt text."""
    import re
    loras = []
    for m in re.finditer(r"<lora:([^:>]+)(?::([^>]*))?(?::([^>]*))?>", text):
        name = m.group(1)
        w1 = m.group(2) or ""
        w2 = m.group(3) or ""
        entry = name
        if w1:
            entry += f":{w1}"
        if w2:
            entry += f":{w2}"
        loras.append(entry)
    return loras


# ComfyUI 节点类型丰富，正向/负向提示词可能存在于多种节点。
# 除标准 CLIPTextEncode 外，fexli-util-node-comfyui 的 FETextInput 用 input 字段存文本，
# 且常作为正向词源头被 CLIPTextEncode 引用。下面是常见的文本承载节点候选集。
_TEXT_NODE_TYPES = {
    "CLIPTextEncode",
    "CLIPTextEncodeSDXL",
    "CLIPTextEncodeSDXLRefiner",
    "T5TextEncode",
    "CLIPEncodeForDit",
    "FETextInput",          # fexli-util: 正向词常存于此节点的 input 字段
    "SeedablePromptNode",   # rgthree / 其他插件
    "PromptAlert",
    "TextEncodeTokenizer",
}

# 文本字段候选名（不同节点把提示词放在不同字段）
_TEXT_FIELDS = ("text", "input", "string", "value", "prompt_text", "positive", "negative")

# 可能承载提示词的采样器节点（含 Advanced 变体）
_SAMPLER_NODE_TYPES = {"KSampler", "KSamplerAdvanced", "KSamplerSelect"}


def _is_node_ref(value) -> bool:
    """ComfyUI 节点引用形如 ["node_id", output_index]。"""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and str(value[0]).isdigit()
        and isinstance(value[1], int)
    )


def _resolve_text(value, data: dict, _seen: set, _depth: int = 0) -> str:
    """把节点输入字段值解析为实际文本字符串。

    - 字符串直接返回
    - 节点引用 ["id", idx] 递归追溯到被引用节点的文本字段
    - 列表/字典等无法解析的值返回空串（绝不抛错，避免 join 崩溃）

    设有递归深度与已访问集合保护，防止循环引用。
    """
    if _depth > 8 or not value:
        return ""
    if isinstance(value, str):
        return value
    if _is_node_ref(value):
        node_id = value[0]
        if node_id in _seen:
            return ""
        _seen.add(node_id)
        node = data.get(node_id)
        if not isinstance(node, dict):
            return ""
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {}) if isinstance(node.get("inputs"), dict) else {}
        # 文本节点：取文本字段
        if cls in _TEXT_NODE_TYPES:
            for fld in _TEXT_FIELDS:
                if fld in inputs:
                    resolved = _resolve_text(inputs[fld], data, _seen, _depth + 1)
                    if resolved:
                        return resolved
        # 非文本节点（如 FEEncLoraAutoLoader）：尝试其 prompt/text/input 等引用字段继续追溯
        for fld in ("prompt", "text", "input", "string", "value"):
            if fld in inputs:
                resolved = _resolve_text(inputs[fld], data, _seen, _depth + 1)
                if resolved:
                    return resolved
        return ""
    # 其它类型（int/float/dict/非引用 list）一律视为非文本
    return ""


def _collect_text_nodes(data: dict) -> list:
    """收集承载文本的节点：(node_id_str, cls, resolved_text, is_native)。

    - is_native=True：节点文本字段是原生字符串（如 CLIPTextEncode 直接写 text、
      FETextInput 直接写 input）
    - is_native=False：节点文本字段是节点引用，文本是追溯得到的（如 CLIPTextEncode
      的 text=["39",2] 指向 FETextInput）

    归类时优先用原生节点；引用节点若其解析文本与某原生节点重复则后续去重。
    统一使用字符串 node_id 作为 key，与 KSampler 引用 ref[0]（字符串）保持一致。
    """
    results = []
    for node_id, node in data.items():
        if not isinstance(node, dict):
            continue
        cls = node.get("class_type", "")
        if cls not in _TEXT_NODE_TYPES:
            continue
        inputs = node.get("inputs", {})
        if not isinstance(inputs, dict):
            continue
        for fld in _TEXT_FIELDS:
            if fld not in inputs:
                continue
            raw = inputs[fld]
            is_native = isinstance(raw, str)
            if is_native:
                if raw:
                    results.append((str(node_id), cls, raw, True))
                    break
            else:
                resolved = _resolve_text(raw, data, {str(node_id)})
                if resolved:
                    results.append((str(node_id), cls, resolved, False))
                    break
    return results


def _parse_comfyui_prompt(prompt_json: str) -> ImageMetadata:
    """Parse ComfyUI prompt JSON (tEXt 'prompt' chunk)."""
    meta = ImageMetadata(source="comfyui")
    meta.raw_params = prompt_json
    try:
        data = json.loads(prompt_json)
    except json.JSONDecodeError:
        return meta

    k_sampler_nodes = []
    model_names = []

    for node_id, node in data.items():
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if cls in _SAMPLER_NODE_TYPES:
            k_sampler_nodes.append(node)
            if cls == "KSampler":
                meta.steps = inputs.get("steps", meta.steps)
                meta.cfg = inputs.get("cfg", meta.cfg)
                meta.seed = inputs.get("seed", meta.seed)
                meta.sampler = inputs.get("sampler_name", meta.sampler)
                meta.scheduler = inputs.get("scheduler", meta.scheduler)
                meta.denoise = inputs.get("denoise", meta.denoise)

        if cls in ("CheckpointLoaderSimple", "UNETLoader"):
            for k, v in inputs.items():
                if isinstance(v, str) and k not in ("weight_dtype",):
                    model_names.append(v)

    if model_names:
        meta.model = model_names[0]

    # 收集所有文本节点（含 FETextInput 等扩展类型，引用已递归解析为字符串）
    text_nodes = _collect_text_nodes(data)
    # node_id(str) -> (text, is_native)，用于按引用判定正负向与去重
    text_by_id = {nid: (txt, native) for nid, _, txt, native in text_nodes}
    # 原生文本集合，用于剔除引用节点的重复文本
    native_texts = {txt for _, _, txt, native in text_nodes if native}

    # Determine positive vs negative from KSampler references.
    # KSampler 的 positive/negative 指向 CLIPTextEncode（或其它编码节点），
    # 该节点的 text 可能是节点引用（如 Anima 工作流正向词经 FETextInput 传入），
    # 因此判定时需沿引用链找到最终承载文本的节点 id。
    positive_ids = set()
    negative_ids = set()
    for ks in k_sampler_nodes:
        for side, ref in (("positive", ks.get("inputs", {}).get("positive")),
                          ("negative", ks.get("inputs", {}).get("negative"))):
            if not _is_node_ref(ref):
                continue
            target_id = ref[0]
            target_set = positive_ids if side == "positive" else negative_ids
            # 若引用节点本身有文本，直接归类
            if target_id in text_by_id:
                target_set.add(target_id)
            # 再沿该节点的 text/prompt 等字段继续追溯到有文本的节点
            resolved_ids = _trace_to_text_node(target_id, data, text_by_id)
            target_set.update(resolved_ids)

    seen_texts = set()
    for node_id, cls, txt, is_native in text_nodes:
        # 去重：引用节点若文本与某原生节点相同，则跳过（避免正向词重复 + LoRA 翻倍）
        if not is_native and txt in native_texts:
            continue
        if txt in seen_texts:
            continue
        seen_texts.add(txt)

        if node_id in negative_ids and node_id not in positive_ids:
            meta.negative_prompts.append(txt)
        elif node_id in positive_ids:
            meta.positive_prompts.append(txt)
        else:
            # 无法判定正负向时默认归正向
            meta.positive_prompts.append(txt)

    if meta.positive_prompts:
        meta.positive_prompt = max(meta.positive_prompts, key=len)
        all_positive = " ".join(meta.positive_prompts)
        meta.loras = _parse_lora_strings(all_positive)
    if meta.negative_prompts:
        meta.negative_prompt = max(meta.negative_prompts, key=len)

    return meta


def _trace_to_text_node(node_id: str, data: dict, text_by_id: dict, _seen: set = None) -> set:
    """沿节点的文本/引用字段追溯到承载文本的节点 id 集合。

    用于 KSampler positive/negative 指向的中间节点（如 FEEncLoraAutoLoader）
    本身不含文本、但其 prompt 字段引用了 FETextInput 的情况。
    """
    if _seen is None:
        _seen = set()
    if node_id in _seen:
        return set()
    _seen.add(node_id)
    result = set()
    node = data.get(node_id)
    if not isinstance(node, dict):
        return result
    inputs = node.get("inputs", {})
    if not isinstance(inputs, dict):
        return result
    for fld in ("prompt", "text", "input", "string", "value", "positive", "negative"):
        val = inputs.get(fld)
        if _is_node_ref(val):
            target = val[0]
            if target in text_by_id:
                result.add(target)
            else:
                result.update(_trace_to_text_node(target, data, text_by_id, _seen))
    return result


def _parse_webui_params(params: str) -> ImageMetadata:
    """Parse Stable Diffusion WebUI/Forge 'parameters' string."""
    import re
    meta = ImageMetadata(source="webui")
    meta.raw_params = params

    # Split by "Negative prompt:" and "Steps:"
    neg_split = params.split("Negative prompt:", 1)
    pos_text = neg_split[0].strip()

    if len(neg_split) > 1:
        remainder = neg_split[1]
        steps_split = remainder.split("\nSteps:", 1)
        if len(steps_split) > 1:
            neg_text = steps_split[0].strip()
            settings_text = "Steps:" + steps_split[1]
        else:
            # Settings might be on the same line
            steps_split2 = remainder.split("Steps:", 1)
            if len(steps_split2) > 1:
                neg_text = steps_split2[0].strip()
                settings_text = "Steps:" + steps_split2[1]
            else:
                neg_text = remainder.strip()
                settings_text = ""
    else:
        neg_text = ""
        settings_text = ""

    meta.positive_prompt = pos_text
    meta.negative_prompt = neg_text
    meta.loras = _parse_lora_strings(pos_text)

    # Parse settings
    if settings_text:
        def _extract(pattern: str, default=""):
            m = re.search(pattern, settings_text)
            return m.group(1).strip() if m else default

        meta.steps = int(_extract(r"Steps:\s*(\d+)", "0"))
        meta.sampler = _extract(r"Sampler:\s*([^,\n]+)")
        meta.scheduler = _extract(r"Schedule type:\s*([^,\n]+)")
        meta.cfg = float(_extract(r"CFG scale:\s*([\d.]+)", "0"))
        meta.seed = int(_extract(r"Seed:\s*(-?\d+)", "-1"))
        meta.size = _extract(r"Size:\s*(\d+x\d+)")
        meta.model = _extract(r"Model:\s*([^,\n]+)")
        meta.model_hash = _extract(r"Model hash:\s*([a-f0-9]+)")

        denoise_match = re.search(r"Denoising strength:\s*([\d.]+)", settings_text)
        if denoise_match:
            meta.denoise = float(denoise_match.group(1))

    return meta


def extract_metadata(filepath: str) -> Optional[ImageMetadata]:
    """Extract prompt metadata from an image file.

    Tries PNG tEXt chunks first (ComfyUI/WebUI), then JPEG EXIF.

    Returns:
        ImageMetadata if any prompt data was found, None otherwise.
    """
    path = Path(filepath)
    if not path.exists():
        logger.error("File not found: %s", filepath)
        return None

    suffix = path.suffix.lower()

    # Try PNG chunks
    if suffix == ".png":
        chunks = _read_png_text_chunks(filepath)

        # ComfyUI format
        if "prompt" in chunks:
            meta = _parse_comfyui_prompt(chunks["prompt"])
            if meta.has_prompt:
                logger.info("Extracted ComfyUI metadata from %s", path.name)
                return meta

        # WebUI / A1111 format
        if "parameters" in chunks:
            meta = _parse_webui_params(chunks["parameters"])
            if meta.has_prompt:
                logger.info("Extracted WebUI metadata from %s", path.name)
                return meta

    # Try JPEG EXIF
    if suffix in (".jpg", ".jpeg"):
        exif = _read_jpeg_exif(filepath)
        if "parameters" in exif:
            meta = _parse_webui_params(exif["parameters"])
            if meta.has_prompt:
                logger.info("Extracted WebUI metadata from JPEG %s", path.name)
                return meta

    logger.info("No AI generation metadata found in %s", path.name)
    return None
