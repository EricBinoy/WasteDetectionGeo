"""Wraps a Hugging Face image-classification pipeline to answer: does this photo show waste?

Assumption: the model id is a binary/multi-label garbage classifier whose labels are strings
like "garbage"/"clean" (or similar). We treat any label containing "garbage", "waste", "trash",
or "dirty" as a positive "is_waste" signal and take its score as confidence. If the top label
doesn't match those keywords, we treat it as not-waste with confidence = 1 - top_score.
"""
from functools import lru_cache
from typing import NamedTuple

from PIL import Image
from transformers import pipeline

MODEL_ID = "nonamelife/garbage-detection-model"
MODEL_VERSION = MODEL_ID

_WASTE_KEYWORDS = ("garbage", "waste", "trash", "dirty", "litter")


class ClassificationResult(NamedTuple):
    is_waste: bool
    confidence: float


@lru_cache(maxsize=1)
def _get_pipeline():
    # Loaded lazily and cached so the process doesn't pull model weights at import time
    # (e.g. during `alembic` commands or tests that don't need CV).
    return pipeline("image-classification", model=MODEL_ID)


def classify_image(image_path: str) -> ClassificationResult:
    clf = _get_pipeline()
    image = Image.open(image_path).convert("RGB")
    results = clf(image)
    if not results:
        return ClassificationResult(is_waste=False, confidence=0.0)

    top = max(results, key=lambda r: r["score"])
    label = top["label"].lower()
    score = float(top["score"])

    if any(keyword in label for keyword in _WASTE_KEYWORDS):
        return ClassificationResult(is_waste=True, confidence=score)
    return ClassificationResult(is_waste=False, confidence=1.0 - score)
