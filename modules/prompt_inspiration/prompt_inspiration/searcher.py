"""Hybrid search engine combining tag filter, TF-IDF, and ONNX semantic search."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from . import config
from .indexer import (
    load_tag_index,
    load_tfidf_index,
    load_embedding_index,
    parse_prompt,
)
from .model_setup import is_available as model_available, compute_embeddings

logger = logging.getLogger(__name__)


# Module-level cache for loaded indices
_cache: Dict[str, object] = {}


def _load_indices(data_dir: Optional[Path] = None) -> None:
    """Load all indices into cache."""
    global _cache
    data_dir = data_dir or config.DATA_DIR

    if "tag_index" not in _cache:
        tag_index, filenames = load_tag_index(data_dir)
        _cache["tag_index"] = tag_index
        _cache["filenames"] = filenames

    if "tfidf" not in _cache:
        tfidf_matrix, vectorizer = load_tfidf_index(data_dir)
        _cache["tfidf"] = tfidf_matrix
        _cache["vectorizer"] = vectorizer

    if "embeddings" not in _cache and model_available():
        try:
            _cache["embeddings"] = load_embedding_index(data_dir)
        except FileNotFoundError:
            logger.warning("Embedding index not found. Semantic search unavailable.")
            _cache["embeddings"] = None

    _cache["data_dir"] = str(data_dir)


def _get_prompt_text(filename: str, prompts_dir: Path) -> str:
    """Read a prompt file and return its text."""
    filepath = prompts_dir / filename
    if not filepath.exists():
        return ""
    return filepath.read_text().strip()


def _tag_filter(tags: List[str], tag_index: Dict) -> Optional[set]:
    """Filter documents matching ALL specified tags (AND logic).

    Returns set of doc_ids, or None if no tags specified (meaning no filter).
    """
    if not tags:
        return None

    matched: Optional[set] = None
    for tag in tags:
        normalized = tag.strip().lower()
        docs = set(tag_index.get(normalized, []))
        if matched is None:
            matched = docs
        else:
            matched &= docs
        if not matched:
            return set()  # early exit
    return matched or set()


def _semantic_search(query: str, top_k: int) -> List[Tuple[int, float]]:
    """ONNX semantic search. Returns [(doc_id, score), ...].

    Falls back to TF-IDF cosine similarity if ONNX unavailable.
    """
    embeddings = _cache.get("embeddings")
    filenames: List[str] = _cache["filenames"]

    if embeddings is not None and model_available():
        query_emb = compute_embeddings([query])
        scores = cosine_similarity(query_emb, embeddings)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_indices]
    else:
        # Fallback: TF-IDF cosine similarity
        vectorizer = _cache["vectorizer"]
        tfidf_matrix = _cache["tfidf"]
        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, tfidf_matrix)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_indices]


def _tag_score(doc_id: int, query_tags: List[str], tag_index: Dict) -> float:
    """Calculate tag match score: fraction of query tags present in doc."""
    if not query_tags:
        return 0.0
    matched = 0
    for tag in query_tags:
        normalized = tag.strip().lower()
        if normalized in tag_index and doc_id in tag_index[normalized]:
            matched += 1
    return matched / len(query_tags)


def _extract_tags(query: str) -> Tuple[str, List[str]]:
    """Extract potential tags from a query. Simple heuristic."""
    stopwords = {"a", "an", "the", "with", "in", "of", "and", "to", "for", "on", "at", "by", "is", "are"}
    words = query.lower().split()
    tags = []
    for w in words:
        w_clean = w.strip(",.!?;:'\"()[]")
        if w_clean and len(w_clean) < 20 and w_clean not in stopwords:
            tags.append(w_clean)
    return query, tags


def search_inspiration(
    query: str,
    tags: Optional[List[str]] = None,
    top_k: int = 10,
    mode: str = "hybrid",
    prompts_dir: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> List[dict]:
    """Search prompt database for inspiration.

    Args:
        query: Natural language description of what to find
        tags: Optional list of tags for exact filtering (AND logic)
        top_k: Number of results to return (max 50)
        mode: "semantic" | "tag" | "hybrid"
        prompts_dir: Override prompts directory (default: config.PROMPTS_DIR)
        data_dir: Override data directory (default: config.DATA_DIR)

    Returns:
        List of dicts with keys: filename, score, tags, description, matched_tags
    """
    prompts_dir = prompts_dir or config.PROMPTS_DIR
    data_dir = data_dir or config.DATA_DIR
    top_k = min(top_k, config.MAX_TOP_K)

    _load_indices(data_dir)
    tag_index: Dict = _cache["tag_index"]
    filenames: List[str] = _cache["filenames"]

    # Determine candidate pool via tag filter
    candidate_ids = _tag_filter(tags or [], tag_index)
    if candidate_ids is not None:
        if len(candidate_ids) == 0:
            _, query_parsed_tags = _extract_tags(query)
            return _format_empty_result(query, tags, query_parsed_tags)
    else:
        candidate_ids = set(range(len(filenames)))

    # Extract tags from query for tag scoring
    _, query_parsed_tags = _extract_tags(query)
    all_query_tags = list(set((tags or []) + query_parsed_tags))

    if mode == "tag":
        # Only tag-match, no semantic ranking
        scored = []
        for doc_id in candidate_ids:
            ts = _tag_score(doc_id, all_query_tags, tag_index)
            scored.append((doc_id, ts))
        scored.sort(key=lambda x: x[1], reverse=True)
    else:
        # Semantic search
        semantic_results = _semantic_search(query, top_k * 3)
        scored = []
        for doc_id, sem_score in semantic_results:
            if doc_id not in candidate_ids:
                continue
            ts = _tag_score(doc_id, all_query_tags, tag_index) if all_query_tags else 0.0
            if mode == "semantic":
                final_score = sem_score
            else:  # hybrid
                final_score = config.HYBRID_ALPHA * sem_score + (1 - config.HYBRID_ALPHA) * ts
            scored.append((doc_id, final_score, sem_score, ts))

        scored.sort(key=lambda x: x[1], reverse=True)

    # Build results
    results = []
    for item in scored[:top_k]:
        if mode in ("semantic", "hybrid"):
            doc_id, final_score, sem_score, ts = item
        else:
            doc_id, final_score = item
            sem_score, ts = 0.0, final_score

        filename = filenames[doc_id]
        text = _get_prompt_text(filename, prompts_dir)
        doc_tags, doc_desc = parse_prompt(text)

        matched = [t for t in all_query_tags
                   if t in tag_index and doc_id in tag_index[t]]

        results.append({
            "filename": filename,
            "score": round(float(final_score), 4),
            "semantic_score": round(float(sem_score), 4),
            "tag_score": round(float(ts), 4),
            "tags": doc_tags[:20],
            "description": doc_desc[:300],
            "matched_tags": matched,
        })

    return results


def _format_empty_result(query: str, tags: Optional[List[str]], parsed_tags: List[str]) -> List[dict]:
    """Return friendly empty result with suggestions."""
    return [{
        "filename": None,
        "score": 0.0,
        "semantic_score": 0.0,
        "tag_score": 0.0,
        "tags": [],
        "description": "No results found for your query.",
        "matched_tags": [],
        "note": (
            f"Try removing some tag filters. "
            f"Query: '{query}', "
            f"Filter tags: {tags}, "
            f"Auto-extracted tags: {parsed_tags}"
        )
    }]
