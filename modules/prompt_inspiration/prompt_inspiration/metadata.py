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
    clip_texts = []

    for node_id, node in data.items():
        cls = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if cls == "KSampler":
            k_sampler_nodes.append(node)
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

        if cls == "CLIPTextEncode":
            text = inputs.get("text", "")
            if text:
                clip_texts.append((int(node_id), text))

    if model_names:
        meta.model = model_names[0]

    # Determine positive vs negative from KSampler references
    positive_ids = set()
    negative_ids = set()
    for ks in k_sampler_nodes:
        ref_pos = ks.get("inputs", {}).get("positive", [None])
        ref_neg = ks.get("inputs", {}).get("negative", [None])
        if ref_pos and ref_pos[0] is not None:
            positive_ids.add(ref_pos[0])
        if ref_neg and ref_neg[0] is not None:
            negative_ids.add(ref_neg[0])

    for node_id, text in clip_texts:
        if node_id in negative_ids:
            meta.negative_prompts.append(text)
        else:
            meta.positive_prompts.append(text)

    if meta.positive_prompts:
        meta.positive_prompt = max(meta.positive_prompts, key=len)
        all_positive = " ".join(meta.positive_prompts)
        meta.loras = _parse_lora_strings(all_positive)
    if meta.negative_prompts:
        meta.negative_prompt = max(meta.negative_prompts, key=len)

    return meta


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
