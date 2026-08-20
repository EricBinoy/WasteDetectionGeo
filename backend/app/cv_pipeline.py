"""Answers: does this photo show illegally dumped waste?

Runs a CLIP-style vision encoder (TinyCLIP, distilled from full CLIP) via ONNX Runtime and compares
the image embedding against two precomputed text-embedding "captions" -- open-vocabulary zero-shot
matching, rather than a fine-tuned garbage classifier, because the available garbage-classification
models on the Hub (e.g. TrashNet-style) are trained on cropped, single-item photos against a plain
background for recycling sorting, and have no "not garbage" class at all -- they can't distinguish a
real dumping photo from an unrelated one.

Why ONNX Runtime instead of the transformers/torch pipeline: on a memory-capped host (512MB), just
importing torch costs ~180MB and transformers another ~65MB before any model is even loaded --
unavoidable fixed overhead regardless of model size. Exporting the vision encoder to ONNX at build
time (backend/scripts/export_model.py, run in the Dockerfile's exporter stage) means the runtime
image never imports torch/transformers at all: onnxruntime's own overhead is ~20-30MB. The two
candidate captions are fixed strings, so their text embeddings are also precomputed at build time --
the runtime never needs the text encoder or a tokenizer either.
"""
import json
import os
from functools import lru_cache
from typing import NamedTuple

import numpy as np
import onnxruntime as ort
from PIL import Image

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "model_assets")

with open(os.path.join(_ASSETS_DIR, "preprocess_config.json")) as _f:
    _CONFIG = json.load(_f)

MODEL_VERSION = _CONFIG["model_version"]
_WASTE_LABEL = _CONFIG["waste_label"]
_NO_WASTE_LABEL = _CONFIG["no_waste_label"]
_TEXT_EMBEDS = np.load(os.path.join(_ASSETS_DIR, "text_embeds.npy"))
_LABELS = [_WASTE_LABEL, _NO_WASTE_LABEL]


class ClassificationResult(NamedTuple):
    is_waste: bool
    confidence: float


@lru_cache(maxsize=1)
def _get_session() -> ort.InferenceSession:
    # Loaded lazily and cached so the process doesn't touch the model at import time
    # (e.g. during `alembic` commands or tests that don't need CV).
    opts = ort.SessionOptions()
    opts.intra_op_num_threads = 1
    opts.inter_op_num_threads = 1
    return ort.InferenceSession(
        os.path.join(_ASSETS_DIR, "vision_encoder.onnx"),
        sess_options=opts,
        providers=["CPUExecutionProvider"],
    )


def _preprocess(image: Image.Image) -> np.ndarray:
    size = _CONFIG["image_size"]
    image = image.convert("RGB").resize((size, size), Image.BICUBIC)
    arr = np.asarray(image).astype(np.float32) / 255.0
    mean = np.array(_CONFIG["mean"], dtype=np.float32)
    std = np.array(_CONFIG["std"], dtype=np.float32)
    arr = (arr - mean) / std
    arr = arr.transpose(2, 0, 1)  # HWC -> CHW
    return arr[np.newaxis, :, :, :].astype(np.float32)


def classify_image(image_path: str) -> ClassificationResult:
    session = _get_session()
    image = Image.open(image_path)
    pixel_values = _preprocess(image)

    image_embeds = session.run(None, {"pixel_values": pixel_values})[0]
    image_embeds = image_embeds / np.linalg.norm(image_embeds, axis=-1, keepdims=True)

    logits = _CONFIG["logit_scale"] * (image_embeds @ _TEXT_EMBEDS.T)[0]
    exp = np.exp(logits - np.max(logits))
    probs = exp / exp.sum()

    idx = int(np.argmax(probs))
    is_waste = _LABELS[idx] == _WASTE_LABEL
    return ClassificationResult(is_waste=is_waste, confidence=float(probs[idx]))
