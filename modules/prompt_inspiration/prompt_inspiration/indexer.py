"""Index builder for prompt inspiration tool."""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

from scipy.sparse import csr_matrix, load_npz, save_npz
from sklearn.feature_extraction.text import TfidfVectorizer

import numpy as np

from . import config
from .model_setup import compute_embeddings


def parse_prompt(text: str) -> Tuple[List[str], str]:
    """Split a prompt line into (tags, description).

    Tags are short comma-separated keywords; description is the natural language part.
    Heuristic: entries with >4 words starting with capital or article are description.
    """
    parts = [p.strip() for p in text.strip().split(",")]
    tags: List[str] = []
    desc_parts: List[str] = []
    for p in parts:
        if not p:
            continue
        words = p.split()
        is_desc = False
        if len(words) > 4:
            first_word = words[0]
            if first_word[0].isupper() or first_word.lower() in ("a", "an", "the"):
                is_desc = True
        if is_desc:
            desc_parts.append(p)
        else:
            tags.append(p)
    description = ", ".join(desc_parts)
    return tags, description


def list_prompt_files(prompts_dir: Path) -> List[Path]:
    """Return sorted list of .txt files in prompts directory."""
    return sorted(prompts_dir.glob("*.txt"))


def build_tag_index(prompts_dir: Path) -> Tuple[Dict[str, List[int]], List[str], Dict[str, str]]:
    """Build inverted index from prompt tag data.

    Returns:
        tag_index: {tag: [doc_id, ...]}
        filenames: [filename, ...] (index = doc_id)
        descriptions: {filename: description_text}
    """
    files = list_prompt_files(prompts_dir)
    filenames = [f.name for f in files]
    descriptions: Dict[str, str] = {}
    tag_index: Dict[str, List[int]] = {}

    for doc_id, filepath in enumerate(files):
        text = filepath.read_text().strip()
        tags, desc = parse_prompt(text)
        descriptions[filepath.name] = desc
        for tag in tags:
            normalized = tag.strip().lower()
            if normalized:
                tag_index.setdefault(normalized, []).append(doc_id)

    return tag_index, filenames, descriptions


def save_tag_index(tag_index: Dict, filenames: List[str], data_dir: Path) -> None:
    """Save tag index and filenames to disk."""
    data_dir.mkdir(parents=True, exist_ok=True)
    tags_path = data_dir / "tags.index.json"
    filenames_path = data_dir / "filenames.json"
    with open(tags_path, "w") as f:
        json.dump(tag_index, f, ensure_ascii=False, indent=2)
    with open(filenames_path, "w") as f:
        json.dump(filenames, f, ensure_ascii=False)


def load_tag_index(data_dir: Path) -> Tuple[Dict[str, List[int]], List[str]]:
    """Load tag index and filenames from disk."""
    tags_path = data_dir / "tags.index.json"
    filenames_path = data_dir / "filenames.json"
    with open(tags_path) as f:
        tag_index = json.load(f)
    with open(filenames_path) as f:
        filenames = json.load(f)
    return tag_index, filenames


def build_tfidf_index(filenames: List[str], prompts_dir: Path) -> Tuple[csr_matrix, TfidfVectorizer]:
    """Build TF-IDF index from prompt files."""
    texts = []
    for name in filenames:
        text = (prompts_dir / name).read_text().strip()
        if not text:
            text = "(empty)"
        texts.append(text)

    vectorizer = TfidfVectorizer(
        ngram_range=config.TFIDF_NGRAM_RANGE,
        max_features=config.TFIDF_MAX_FEATURES,
        stop_words="english",
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    return tfidf_matrix, vectorizer


def save_tfidf_index(tfidf_matrix: csr_matrix, vectorizer: TfidfVectorizer, data_dir: Path) -> None:
    """Save TF-IDF matrix and vectorizer to disk."""
    data_dir.mkdir(parents=True, exist_ok=True)
    save_npz(data_dir / "tfidf.npz", tfidf_matrix)
    with open(data_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)


def load_tfidf_index(data_dir: Path) -> Tuple[csr_matrix, TfidfVectorizer]:
    """Load TF-IDF matrix and vectorizer from disk."""
    tfidf_matrix = load_npz(data_dir / "tfidf.npz")
    with open(data_dir / "vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    return tfidf_matrix, vectorizer


def build_embedding_index(filenames: List[str], prompts_dir: Path) -> np.ndarray:
    """Build ONNX embedding index from prompt files.

    Returns:
        embeddings: (n_docs, embedding_dim) array
    """
    texts = []
    for name in filenames:
        text = (prompts_dir / name).read_text().strip()
        if not text:
            text = "(empty)"
        texts.append(text)

    embeddings = compute_embeddings(texts)
    return embeddings


def save_embedding_index(embeddings: np.ndarray, data_dir: Path) -> None:
    """Save embeddings to disk."""
    data_dir.mkdir(parents=True, exist_ok=True)
    np.save(data_dir / "embeddings.npy", embeddings)


def load_embedding_index(data_dir: Path) -> np.ndarray:
    """Load embeddings from disk."""
    return np.load(data_dir / "embeddings.npy")


import logging
from typing import Optional

logger = logging.getLogger(__name__)


def build_all(data_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None) -> None:
    """Build all indices (tag, TF-IDF, embedding) from prompt files.

    Args:
        data_dir: output directory for index files (default: config.DATA_DIR)
        prompts_dir: input directory of .txt prompt files (default: config.PROMPTS_DIR)
    """
    from . import config as cfg
    prompts_dir = prompts_dir or cfg.PROMPTS_DIR
    data_dir = data_dir or cfg.DATA_DIR

    if not prompts_dir.is_dir():
        raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

    logger.info("Building tag index...")
    tag_index, filenames, _ = build_tag_index(prompts_dir)
    save_tag_index(tag_index, filenames, data_dir)
    logger.info("Tag index: %d tags, %d docs", len(tag_index), len(filenames))

    logger.info("Building TF-IDF index...")
    tfidf_matrix, vectorizer = build_tfidf_index(filenames, prompts_dir)
    save_tfidf_index(tfidf_matrix, vectorizer, data_dir)
    logger.info("TF-IDF matrix: %s", tfidf_matrix.shape)

    from .model_setup import is_available as model_available
    if model_available():
        logger.info("Building embedding index (ONNX)...")
        embeddings = build_embedding_index(filenames, prompts_dir)
        save_embedding_index(embeddings, data_dir)
        logger.info("Embedding index: %s", embeddings.shape)
    else:
        logger.warning(
            "ONNX model not found. Skipping embedding index. "
            "Run 'prompt-inspiration setup' after installing optional deps to enable semantic search."
        )

    logger.info("All indices built successfully.")
