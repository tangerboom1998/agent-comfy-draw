"""
_env.py — Shared environment configuration for comfyui-draw project.

All paths are read from environment variables with sensible defaults.
Import this to get consistent paths across all scripts — no more hardcoded paths.

Environment variables:
    LORA_MODEL_DIR  - LoRA model storage root (default: /opt/comfyui/models/loras)
    COMFYUI_ROOT    - ComfyUI installation root  (default: /opt/comfyui/ComfyUI)

Directory structure:
    $LORA_MODEL_DIR/
    ├── anima/                  # 默认模型类型
    │   ├── 人物/
    │   ├── 画风/
    │   └── 服装/
    ├── illustrious&noob/
    │   ├── 人物/
    │   ├── 画风/
    │   └── 服装/
    └── z_image_turbo/
        ├── 人物/
        ├── 画风/
        └── 服装/

Model type is auto-detected from LoRA filename via keyword matching (see MODEL_TYPE_RULES).

Usage:
    import sys, os
    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, _PROJECT_ROOT)
    from _env import LORA_MODEL_DIR, COMFYUI_ROOT, get_lora_dir, find_lora_file
"""

import os as _os

# ── Load .env from project root (if present) ──
_ENV_DIR = _os.path.dirname(_os.path.abspath(__file__))
_ENV_FILE = _os.path.join(_ENV_DIR, '.env')
if _os.path.exists(_ENV_FILE):
    with open(_ENV_FILE, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                _os.environ.setdefault(_k.strip(), _v.strip())

# ── LoRA 模型存储根目录 ──
LORA_MODEL_DIR: str = _os.environ.get(
    "LORA_MODEL_DIR",
    "/opt/comfyui/models/loras"
)

# ── ComfyUI 安装根目录 ──
COMFYUI_ROOT: str = _os.environ.get(
    "COMFYUI_ROOT",
    "/opt/comfyui/ComfyUI"
)

# ── 分类子目录名 ──
CATEGORY_DIRS: tuple[str, ...] = ("人物", "画风", "服装", "其他",
                                   "z-image", "z-flux", "wan", "lumina", "qwen", "qwenedit")

# ── 模型类型检测规则 ──
# (关键字, 模型类型目录名)，按优先级排序，首次匹配生效
# 关键字匹配忽略大小写
MODEL_TYPE_RULES: list[tuple[str, str]] = [
    ("z_image", "z_image_turbo"),
    ("turbo", "z_image_turbo"),
    ("noob", "illustrious&noob"),
    ("illustrious", "illustrious&noob"),
    ("anima", "anima"),
]

# 默认模型类型（无关键字匹配时使用）
DEFAULT_MODEL_TYPE: str = "anima"


def detect_model_type(filename: str) -> str:
    """根据文件名关键字检测模型类型。

    Args:
        filename: LoRA 文件名（不含路径，大小写不敏感）

    Returns:
        模型类型目录名，如 'anima', 'illustrious&noob', 'z_image_turbo'
    """
    lower = filename.lower()
    for keyword, model_type in MODEL_TYPE_RULES:
        if keyword in lower:
            return model_type
    return DEFAULT_MODEL_TYPE


def get_lora_dir(category: str, filename: str | None = None) -> str:
    """获取分类目录的完整路径。

    目录结构: $LORA_MODEL_DIR/{model_type}/{category}/

    Args:
        category: 分类名（'人物', '画风', '服装', '其他' 等）
        filename: 可选，LoRA 文件名，用于自动检测 model_type。
                  不提供则返回 $LORA_MODEL_DIR/{category}/（旧版扁平结构）。

    Returns:
        完整路径
    """
    if filename:
        model_type = detect_model_type(filename)
        return _os.path.join(LORA_MODEL_DIR, model_type, category)
    else:
        return _os.path.join(LORA_MODEL_DIR, category)


def iter_lora_subdirs(category: str) -> list[str]:
    """遍历所有存在的 model_type/{category} 子目录。

    扫描 $LORA_MODEL_DIR 下的每个 model_type 子目录，
    返回存在对应 category 子目录的完整路径列表。
    同时兼容旧版扁平结构（$LORA_MODEL_DIR/{category}/）。

    Args:
        category: 分类名（'人物', '画风', '服装', '其他' 等）

    Returns:
        存在的目录路径列表
    """
    dirs: list[str] = []
    if not _os.path.isdir(LORA_MODEL_DIR):
        return dirs
    for entry in sorted(_os.listdir(LORA_MODEL_DIR)):
        entry_path = _os.path.join(LORA_MODEL_DIR, entry)
        if not _os.path.isdir(entry_path):
            continue
        subdir = _os.path.join(entry_path, category)
        if _os.path.isdir(subdir):
            dirs.append(subdir)
    return dirs


def find_lora_file(filename: str, category: str | None = None) -> str | None:
    """在所有 model_type 目录中查找 LoRA 文件。

    支持带或不带 .safetensors 后缀的文件名。

    Args:
        filename: LoRA 文件名（stem 或含 .safetensors 后缀）
        category: 可选，限定分类目录（'人物', '画风', '服装', '其他'）

    Returns:
        找到的完整路径，未找到返回 None
    """
    safetensors_name = filename if filename.endswith(".safetensors") else filename + ".safetensors"

    if category:
        candidates = iter_lora_subdirs(category)
    else:
        candidates = []
        for cat in CATEGORY_DIRS:
            candidates.extend(iter_lora_subdirs(cat))

    for dirpath in candidates:
        fpath = _os.path.join(dirpath, safetensors_name)
        if _os.path.isfile(fpath):
            return fpath

    return None
