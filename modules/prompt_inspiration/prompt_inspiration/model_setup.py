"""ONNX model download and embedding computation."""

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
from numpy import ndarray

from . import config

logger = logging.getLogger(__name__)


def _check_onnx_model_exists() -> bool:
    """Check if the ONNX model directory exists and contains .onnx files."""
    path = config.ONNX_MODEL_PATH
    if not path.is_dir():
        return False
    return any(path.rglob("*.onnx"))


def download_model() -> None:
    """Download the pre-exported ONNX model and tokenizer from HuggingFace Hub.

    Uses huggingface_hub to download the Xenova/all-MiniLM-L6-v2 model
    which is already exported to ONNX format. No PyTorch or optimum needed.
    """
    if _check_onnx_model_exists():
        logger.info("ONNX model already exists at %s", config.ONNX_MODEL_PATH)
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        raise ImportError(
            "huggingface_hub is required. Install: pip install huggingface_hub"
        )

    config.ONNX_MODEL_PATH.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading ONNX model from %s ...", config.ONNX_MODEL_ID)
    snapshot_download(
        repo_id=config.ONNX_MODEL_ID,
        local_dir=str(config.ONNX_MODEL_PATH),
        local_dir_use_symlinks=False,
        resume_download=True,
    )
    logger.info("ONNX model saved to %s", config.ONNX_MODEL_PATH)


def _get_tokenizer_and_session() -> Tuple:
    """Load tokenizer and create ONNX inference session.

    Returns:
        (tokenizer, inference_session)
    """
    from transformers import AutoTokenizer
    import onnxruntime

    tokenizer = AutoTokenizer.from_pretrained(str(config.ONNX_MODEL_PATH))

    onnx_files = list(config.ONNX_MODEL_PATH.rglob("*.onnx"))
    if not onnx_files:
        raise FileNotFoundError(f"No .onnx files found in {config.ONNX_MODEL_PATH}")
    onnx_path = str(onnx_files[0])

    session = onnxruntime.InferenceSession(onnx_path)
    return tokenizer, session


def _mean_pooling(token_embeddings: ndarray, attention_mask: ndarray) -> ndarray:
    mask = attention_mask[:, :, np.newaxis].astype(np.float32)
    masked = token_embeddings * mask
    summed = masked.sum(axis=1)
    counts = mask.sum(axis=1).clip(min=1e-9)
    return summed / counts


def _normalize(embeddings: ndarray) -> ndarray:
    """L2 normalize embeddings along axis 1."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = norms.clip(min=1e-12)
    return embeddings / norms


def compute_embeddings(texts: List[str], batch_size: int = 32) -> ndarray:
    """Compute normalized embeddings for a list of texts using ONNX model.

    Args:
        texts: List of text strings to embed.
        batch_size: Number of texts to process per batch.

    Returns:
        numpy array of shape (n_texts, 384) with normalized embeddings.

    Raises:
        RuntimeError: If the ONNX model has not been downloaded.
    """
    if not _check_onnx_model_exists():
        raise RuntimeError(
            "ONNX model not found. Run download_model() or install the model first."
        )

    tokenizer, session = _get_tokenizer_and_session()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            return_tensors="np",
        )

        onnx_inputs = {
            "input_ids": inputs["input_ids"],
            "attention_mask": inputs["attention_mask"],
        }
        if "token_type_ids" in inputs:
            onnx_inputs["token_type_ids"] = inputs["token_type_ids"]
        outputs = session.run(None, onnx_inputs)
        token_embeddings = outputs[0]

        pooled = _mean_pooling(token_embeddings, inputs["attention_mask"])
        normalized = _normalize(pooled)
        all_embeddings.append(normalized)

    return np.vstack(all_embeddings)


def is_available() -> bool:
    """Check if the ONNX model is available for use."""
    return _check_onnx_model_exists()
