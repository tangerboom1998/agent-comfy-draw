"""Agent tool interface for Claude Code function calling.

Exposes search_inspiration as a structured tool that agents can call
to retrieve prompt inspiration from the tagging database.
"""

from typing import Dict, List, Optional

from .searcher import search_inspiration as _search


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
