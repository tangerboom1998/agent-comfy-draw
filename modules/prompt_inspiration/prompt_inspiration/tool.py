"""Agent tool interface for Claude Code function calling.

Exposes search_inspiration and extract_image_metadata as structured tools
that agents can call to retrieve prompt inspiration from the tagging database
and extract prompts from AI-generated images.
"""

from typing import Dict, List, Optional

from .searcher import search_inspiration as _search
from .metadata import extract_metadata as _extract


TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_inspiration",
        "description": (
            "Search the image tagging prompt database for creative inspiration. "
            "Describe the visual concept, style, character, or scene you need, "
            "and optionally filter by tags. Returns the most relevant prompt examples "
            "with their tags, descriptions, and relevance scores."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language description of what you're looking for. "
                        "E.g., 'a cyberpunk warrior with neon hair', "
                        "'a mecha robot in battle', 'a fantasy elf queen'"
                    ),
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Optional tag filters (AND logic). Only prompts matching ALL "
                        "specified tags will be returned. E.g., ['1girl', 'solo', 'portrait']"
                    ),
                },
                "top_k": {
                    "type": "integer",
                    "default": 10,
                    "maximum": 50,
                    "description": "Number of results to return (max 50)",
                },
                "mode": {
                    "type": "string",
                    "enum": ["semantic", "tag", "hybrid"],
                    "default": "hybrid",
                    "description": (
                        "Search mode: 'semantic' uses vector similarity, "
                        "'tag' uses exact tag matching, 'hybrid' combines both"
                    ),
                },
            },
            "required": ["query"],
        },
    },
}

EXTRACT_METADATA_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "extract_image_metadata",
        "description": (
            "Extract prompt metadata from an AI-generated image file. "
            "Supports ComfyUI (workflow JSON in tEXt chunk) and "
            "Stable Diffusion WebUI/Forge (parameters in tEXt chunk). "
            "Returns the positive/negative prompts, model, LoRA, sampler settings, etc. "
            "Returns null if the image has no generation metadata."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the image file (PNG or JPEG)",
                },
            },
            "required": ["filepath"],
        },
    },
}


def search_inspiration(
    query: str,
    tags: Optional[List[str]] = None,
    top_k: int = 10,
    mode: str = "hybrid",
) -> List[Dict]:
    """Agent-callable search function.

    This is the primary entry point for Claude Code agent tools.
    Delegates to searcher.search_inspiration with default paths.

    Args:
        query: Natural language description of desired content
        tags: Optional list of tags for exact filtering
        top_k: Number of results (max 50)
        mode: 'semantic', 'tag', or 'hybrid'

    Returns:
        List of result dicts with filename, score, tags, description

    Example:
        >>> results = search_inspiration(
        ...     query="a mechanized female warrior with glowing blue eyes",
        ...     tags=["mecha", "1girl"],
        ...     top_k=5,
        ...     mode="hybrid"
        ... )
        >>> results[0]["filename"]
        'image9914922.txt'
    """
    return _search(
        query=query,
        tags=tags,
        top_k=top_k,
        mode=mode,
    )


def extract_image_metadata(filepath: str) -> Optional[Dict]:
    """Agent-callable metadata extraction.

    Extracts prompt metadata from AI-generated images (ComfyUI/WebUI).
    Returns a dict with positive_prompt, negative_prompt, model, loras, etc.
    Returns None if no generation metadata is found.

    Args:
        filepath: Path to the image file (PNG or JPEG)

    Returns:
        Dict with extracted metadata, or None if no metadata found.
    """
    meta = _extract(filepath)
    if meta is None or not meta.has_prompt:
        return None
    return {
        "source": meta.source,
        "positive_prompt": meta.best_positive(),
        "negative_prompt": meta.best_negative(),
        "model": meta.model,
        "model_hash": meta.model_hash,
        "loras": meta.loras,
        "sampler": meta.sampler,
        "steps": meta.steps,
        "cfg": meta.cfg,
        "seed": meta.seed,
        "scheduler": meta.scheduler,
        "denoise": meta.denoise,
        "size": meta.size,
    }
