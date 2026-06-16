"""VLM tagger - natural language caption generation via OpenAI-compatible API.

Uses a multimodal LLM API (e.g. Qwen-VL, GPT-4V, etc.) to generate
natural language descriptions or comma-separated tags from images.
"""

import base64
import io
import logging
from pathlib import Path
from typing import List, Optional, Tuple

from .. import config

from openai import OpenAI
from PIL import Image

logger = logging.getLogger(__name__)

# Default prompts - comma-separated tags format, no sentences, no periods
DEFAULT_TAG_PROMPT = (
    "Describe this image using comma-separated tags for AI training tagging. "
    "Include: subject, appearance, clothing, pose, expression, background, "
    "art style, lighting, composition, color palette. "
    "Output only comma-separated tags, no sentences, no periods, no prefixes."
)

DEFAULT_CAPTION_PROMPT = (
    "Describe this image using comma-separated descriptive phrases for AI training. "
    "Include: main subject and its details, appearance, clothing, pose, expression, "
    "background setting, art style, lighting, atmosphere, composition, color palette. "
    "Output only comma-separated phrases, no sentences, no periods, no prefixes."
)


class VLMTagger:
    """Vision-Language Model tagger for natural language caption generation.

    Connects to any OpenAI-compatible API endpoint that supports
    image understanding (vision) capabilities.

    Args:
        api_base: Base URL of the OpenAI-compatible API.
        api_key: API key for authentication.
        model: Model name to use.
        max_tokens: Maximum tokens for generation.
        temperature: Generation temperature.
    """

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.7,
        top_p: float = 0.9,
        extra_params: Optional[dict] = None,
    ):
        self.api_base = (api_base or config.VLM_API_BASE).rstrip("/")
        self.api_key = api_key or config.VLM_API_KEY
        self.model = model or config.VLM_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.extra_params = extra_params or {}

        self.client = OpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
        )

        # If model is "auto", fetch the first available model
        if self.model == "auto":
            self.model = self._resolve_model()
            logger.info("Auto-selected model: %s", self.model)

    def _resolve_model(self) -> str:
        """Fetch available models and return the first one."""
        try:
            models = self.client.models.list()
            available = [m.id for m in models.data]
            if not available:
                raise RuntimeError("No models available from API")
            logger.info("Available models: %s", available)
            return available[0]
        except Exception as e:
            logger.warning("Failed to fetch model list: %s. Using 'default'.", e)
            return "default"

    def _encode_image(self, image_path: str | Path) -> Tuple[str, str]:
        """Encode image to base64, return (base64_str, mime_type).

        Non-JPEG/PNG images are converted to JPEG first.
        """
        path = Path(image_path)
        ext = path.suffix.lower()

        # Direct encode for jpg/png
        if ext in (".jpg", ".jpeg", ".png"):
            with open(path, "rb") as f:
                data = f.read()
            mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"
            return base64.b64encode(data).decode("utf-8"), mime

        # Convert other formats (webp, bmp, etc.) to JPEG
        with Image.open(path) as img:
            img = img.convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8"), "image/jpeg"

    def tag_image(
        self,
        image_path: str | Path,
        prompt: Optional[str] = None,
        mode: str = "tags",
    ) -> str:
        """Generate tags or caption for an image using VLM.

        Args:
            image_path: Path to the image file.
            prompt: Custom prompt override. If None, uses default for the mode.
            mode: 'tags' for comma-separated tags, 'caption' for natural language.

        Returns:
            Generated text (tags or caption).
        """
        if prompt is None:
            prompt = DEFAULT_TAG_PROMPT if mode == "tags" else DEFAULT_CAPTION_PROMPT

        b64, mime = self._encode_image(image_path)

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ]

        body = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        body.update(self.extra_params)

        response = self.client.chat.completions.create(**body)
        msg = response.choices[0].message
        result = (msg.content or "").strip()

        # Handle reasoning models (e.g. Qwen3) where content may be empty
        if not result:
            reasoning = getattr(msg, "reasoning_content", None) or ""
            if reasoning.strip():
                # Try to extract result from the tail of reasoning
                tail = reasoning.rstrip()[-600:]
                lines = tail.split("\n")
                for line in reversed(lines):
                    stripped = line.strip()
                    if stripped and len(stripped) > 20:
                        result = stripped
                        break
                if not result:
                    result = reasoning.rstrip()[-300:]

        return self._clean_output(result)

    @staticmethod
    def _clean_output(text: str) -> str:
        """Ensure output is comma-separated with no trailing periods."""
        # Remove trailing period(s)
        text = text.rstrip(".")
        # If there's a period mid-text, it might be a sentence - replace with comma
        # But only if it looks like a sentence separator (period + space)
        import re
        text = re.sub(r'\.\s+', ', ', text)
        # Clean up any double commas
        while ", ," in text:
            text = text.replace(", ,", ",")
        while ",," in text:
            text = text.replace(",,", ",")
        return text.strip(", ")

    def tag_batch(
        self,
        image_paths: List[Path | str],
        prompt: Optional[str] = None,
        mode: str = "tags",
    ) -> List[Tuple[str, str]]:
        """Tag multiple images. Returns [(image_path, result_str), ...]."""
        results = []
        for path in image_paths:
            result = self.tag_image(path, prompt=prompt, mode=mode)
            results.append((str(path), result))
        return results
