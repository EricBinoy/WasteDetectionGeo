"""Wraps a Hugging Face zero-shot image-classification pipeline to answer: does this photo
show illegally dumped waste?

We use CLIP zero-shot classification rather than a fine-tuned garbage classifier because the
available garbage-classification models on the Hub (e.g. TrashNet-style) are trained on cropped,
single-item photos against a plain background for recycling sorting, and have no "not garbage"
class at all -- they can't distinguish a real dumping photo from an unrelated one. CLIP's
open-vocabulary matching generalizes much better to real-world street photos and gives us a
genuine positive/negative signal via two candidate captions.
"""
from functools import lru_cache
from typing import NamedTuple

from PIL import Image
from transformers import pipeline

MODEL_ID = "openai/clip-vit-base-patch32"
MODEL_VERSION = MODEL_ID

_WASTE_LABEL = "a photo of illegally dumped garbage or waste on the ground"
_NO_WASTE_LABEL = "a photo of a clean area with no garbage or waste"
_CANDIDATE_LABELS = [_WASTE_LABEL, _NO_WASTE_LABEL]


class ClassificationResult(NamedTuple):
    is_waste: bool
    confidence: float


@lru_cache(maxsize=1)
def _get_pipeline():
    # Loaded lazily and cached so the process doesn't pull model weights at import time
    # (e.g. during `alembic` commands or tests that don't need CV).
    return pipeline("zero-shot-image-classification", model=MODEL_ID)


def classify_image(image_path: str) -> ClassificationResult:
    clf = _get_pipeline()
    image = Image.open(image_path).convert("RGB")
    results = clf(image, candidate_labels=_CANDIDATE_LABELS)
    if not results:
        return ClassificationResult(is_waste=False, confidence=0.0)

    top = max(results, key=lambda r: r["score"])
    is_waste = top["label"] == _WASTE_LABEL
    return ClassificationResult(is_waste=is_waste, confidence=float(top["score"]))
