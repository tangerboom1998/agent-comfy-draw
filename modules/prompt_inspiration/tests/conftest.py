"""Test fixtures."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

FIXTURE_PROMPTS = {
    "test_mecha.txt": (
        "mecha, robot, solo, science fiction, gun, holding weapon, "
        "A large robot standing in a field with a gun, cinematic lighting, highly detailed"
    ),
    "test_girl.txt": (
        "1girl, solo, portrait, brown hair, blue eyes, "
        "A young woman with brown hair and blue eyes, soft lighting, realistic style"
    ),
    "test_cyberpunk.txt": (
        "cyberpunk, city, night, neon lights, rain, "
        "A cyberpunk city street at night with neon signs reflecting on wet pavement, blade runner style"
    ),
    "test_fantasy.txt": (
        "fantasy, dragon, fire, epic, battle, "
        "A dragon breathing fire in an epic battle scene, dark fantasy style, dramatic lighting"
    ),
}


@pytest.fixture
def prompts_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with fixture prompt files."""
    tmp = Path(tempfile.mkdtemp())
    for name, content in FIXTURE_PROMPTS.items():
        (tmp / name).write_text(content)
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def data_dir() -> Generator[Path, None, None]:
    """Create a temporary data directory."""
    tmp = Path(tempfile.mkdtemp())
    try:
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
