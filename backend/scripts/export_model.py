"""Build-time-only script: exports TinyCLIP's vision encoder to ONNX and precomputes text
embeddings for our two fixed candidate labels, so the runtime image never needs to import
torch/transformers or run the text encoder -- see backend/app/cv_pipeline.py.

Run once during the Docker build's exporter stage; output files are copied into the
runtime stage and this script (and its torch/transformers dependency) is discarded.
"""
import json
import os

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

MODEL_ID = "wkcn/TinyCLIP-ViT-8M-16-Text-3M-YFCC15M"
WASTE_LABEL = "a photo of illegally dumped garbage or waste on the ground"
NO_WASTE_LABEL = "a photo of a clean area with no garbage or waste"

OUT_DIR = os.environ.get("EXPORT_OUT_DIR", ".")


class VisionEncoder(torch.nn.Module):
    def __init__(self, clip_model: CLIPModel):
        super().__init__()
        self.clip_model = clip_model

    def forward(self, pixel_values):
        image_embeds = self.clip_model.get_image_features(pixel_values=pixel_values)
        return image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # attn_implementation="eager" avoids CLIPSdpaAttention's scaled_dot_product_attention op,
    # whose ONNX symbolic export is broken in this torch version.
    model = CLIPModel.from_pretrained(MODEL_ID, attn_implementation="eager")
    processor = CLIPProcessor.from_pretrained(MODEL_ID)
    model.eval()

    text_inputs = processor(text=[WASTE_LABEL, NO_WASTE_LABEL], return_tensors="pt", padding=True)
    with torch.no_grad():
        text_embeds = model.get_text_features(**text_inputs)
        text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
    np.save(os.path.join(OUT_DIR, "text_embeds.npy"), text_embeds.numpy().astype(np.float32))

    image_size = processor.image_processor.crop_size["height"]
    dummy_input = torch.randn(1, 3, image_size, image_size)

    wrapper = VisionEncoder(model)
    wrapper.eval()
    torch.onnx.export(
        wrapper,
        dummy_input,
        os.path.join(OUT_DIR, "vision_encoder.onnx"),
        input_names=["pixel_values"],
        output_names=["image_embeds"],
        dynamic_axes={"pixel_values": {0: "batch"}, "image_embeds": {0: "batch"}},
        opset_version=14,
    )

    config = {
        "image_size": image_size,
        "mean": processor.image_processor.image_mean,
        "std": processor.image_processor.image_std,
        "logit_scale": model.logit_scale.exp().item(),
        "waste_label": WASTE_LABEL,
        "no_waste_label": NO_WASTE_LABEL,
        "model_version": MODEL_ID,
    }
    with open(os.path.join(OUT_DIR, "preprocess_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    print("Export complete:", os.listdir(OUT_DIR))


if __name__ == "__main__":
    main()
