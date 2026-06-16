"""WD14 tagger - Danbooru-style tag prediction using WaifuDiffusion ONNX model.

References:
  - https://github.com/SmilingWolf/wd-tagger
  - Excel_tagger.ipynb in project tagger/
"""

import csv
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import onnxruntime as ort
from PIL import Image

logger = logging.getLogger(__name__)

# Default path to the WD model
_MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "tagger_models"
_DEFAULT_ONNX = _MODELS_DIR / "wd-v1-4-convnextv2-tagger-v2.onnx"
_DEFAULT_CSV = _MODELS_DIR / "wd-v1-4-convnextv2-tagger-v2.csv"

# Categories in the CSV
CATEGORY_GENERAL = "0"
CATEGORY_CHARACTER = "4"
CATEGORY_RATING = "9"


class WDTagger:
    """WaifuDiffusion tagger for Danbooru-style tag prediction.

    Uses a local ONNX model to predict tags from images.
    Supports configurable thresholds, tag filtering, and replacement.

    Args:
        model_path: Path to the .onnx model file.
        csv_path: Path to the .csv tag definitions file.
        providers: ONNX Runtime providers (default: CPU).
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        csv_path: Optional[Path] = None,
        providers: Optional[List[str]] = None,
    ):
        self.model_path = model_path or _DEFAULT_ONNX
        self.csv_path = csv_path or _DEFAULT_CSV

        if not self.model_path.exists():
            raise FileNotFoundError(f"WD model not found: {self.model_path}")
        if not self.csv_path.exists():
            raise FileNotFoundError(f"WD tags CSV not found: {self.csv_path}")

        self.session = ort.InferenceSession(
            str(self.model_path),
            providers=providers or ["CPUExecutionProvider"],
        )
        self._load_tags()

        # Input shape: [1, 448, 448, 3]
        self.input_height = self.session.get_inputs()[0].shape[1]

    def _load_tags(self):
        """Parse CSV to build tag list and category boundaries."""
        self.tag_names: List[str] = []
        self.general_start = 0
        self.character_start = 0
        self.rating_count = 0  # number of rating tags at the beginning

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            rows = list(reader)

        # First pass: count ratings (category=9) at the start
        for row in rows:
            if row[2] == CATEGORY_RATING:
                self.rating_count += 1
            else:
                break

        # Build tag names list
        for row in rows:
            self.tag_names.append(row[1])

        # Find category boundaries
        self.general_start = self.rating_count
        for i in range(self.rating_count, len(rows)):
            if rows[i][2] == CATEGORY_CHARACTER:
                self.character_start = i
                break
        else:
            self.character_start = len(rows)

    def _preprocess(self, image: Image.Image) -> np.ndarray:
        """Preprocess PIL image to model input format.

        1. Resize maintaining aspect ratio to target height
        2. Pad to square with white
        3. Convert RGB -> BGR float32
        4. Add batch dimension
        """
        target = self.input_height  # 448

        # Resize maintaining aspect ratio
        ratio = target / max(image.size)
        new_size = tuple(int(x * ratio) for x in image.size)
        image = image.resize(new_size, Image.LANCZOS)

        # Pad to square with white
        square = Image.new("RGB", (target, target), (255, 255, 255))
        square.paste(image, ((target - new_size[0]) // 2, (target - new_size[1]) // 2))

        # Convert to numpy BGR float32
        arr = np.array(square, dtype=np.float32)
        arr = arr[:, :, ::-1]  # RGB -> BGR

        # Add batch dimension
        return np.expand_dims(arr, 0)

    def tag_image(
        self,
        image_path: str | Path,
        general_threshold: float = 0.35,
        character_threshold: float = 0.85,
        replace_underscore: bool = True,
        additional_tags: Optional[List[str]] = None,
        exclude_tags: Optional[List[str]] = None,
        replace_tags: Optional[dict] = None,
    ) -> str:
        """Generate Danbooru-style tags for an image.

        Args:
            image_path: Path to the image file.
            general_threshold: Minimum probability for general tags.
            character_threshold: Minimum probability for character tags.
            replace_underscore: Convert underscores to spaces in tag names.
            additional_tags: Tags to always include at the beginning.
            exclude_tags: Tags to exclude from results.
            replace_tags: Dict mapping old_tag -> new_tag for renaming.

        Returns:
            Comma-separated tag string.
        """
        # Load image
        pil = Image.open(image_path).convert("RGB")
        input_data = self._preprocess(pil)

        # Run inference
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name
        probs = self.session.run([output_name], {input_name: input_data})[0][0]

        # Apply tag names
        tagged = list(zip(self.tag_names, probs))

        # Split by category
        general_tags = tagged[self.general_start : self.character_start]
        character_tags = tagged[self.character_start:]

        # Filter by threshold
        active = [
            t for t in character_tags if t[1] > character_threshold
        ] + [
            t for t in general_tags if t[1] > general_threshold
        ]

        # Format tag names
        result = []
        for name, _prob in active:
            if replace_underscore:
                name = name.replace("_", " ")
            # Escape brackets for prompt compatibility
            name = name.replace("(", "\\(").replace(")", "\\)")
            result.append(name)

        # Apply exclude list
        if exclude_tags:
            exclude = [t.strip().lower() for t in exclude_tags]
            result = [t for t in result if t.lower() not in exclude]

        # Apply tag replacement
        if replace_tags:
            result = [replace_tags.get(t, t) for t in result]

        # Add additional tags at the beginning
        if additional_tags:
            result = [t.strip() for t in additional_tags if t.strip()] + result

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for t in result:
            if t and t not in seen:
                seen.add(t)
                deduped.append(t)

        return ", ".join(deduped)

    def tag_batch(
        self,
        image_paths: List[Path | str],
        **kwargs,
    ) -> List[Tuple[str, str]]:
        """Tag multiple images. Returns [(image_path, tags_str), ...]."""
        results = []
        for path in image_paths:
            tags = self.tag_image(path, **kwargs)
            results.append((str(path), tags))
        return results
