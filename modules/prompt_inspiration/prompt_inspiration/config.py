"""Path, parameter and environment variable configuration."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"

# Index files
TAGS_INDEX_PATH = DATA_DIR / "tags.index.json"
TFIDF_MATRIX_PATH = DATA_DIR / "tfidf.npz"
VECTORIZER_PATH = DATA_DIR / "vectorizer.pkl"
EMBEDDINGS_PATH = DATA_DIR / "embeddings.npy"
FILENAMES_PATH = DATA_DIR / "filenames.json"

# ONNX model
ONNX_MODEL_ID = "Xenova/all-MiniLM-L6-v2"
ONNX_MODEL_PATH = MODELS_DIR / "all-MiniLM-L6-v2"

# Search defaults
DEFAULT_TOP_K = 10
MAX_TOP_K = 50
HYBRID_ALPHA = 0.7  # weight for semantic score, 1-alpha for tag match score

# TF-IDF n-gram range
TFIDF_NGRAM_RANGE = (1, 3)
TFIDF_MAX_FEATURES = 10000

# VLM API configuration (from environment variables)
VLM_API_BASE = os.environ.get(
    "VLM_API_BASE",
    "https://token-plan-cn.xiaomimimo.com/v1",
)
VLM_API_KEY = os.environ.get("VLM_API_KEY", "")
VLM_MODEL = os.environ.get("VLM_MODEL", "mimo-v2.5")
