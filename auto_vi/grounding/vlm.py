"""VLM-based grounding strategy using Holo1.5-3B.

Uses a vision-language model to locate any UI element by description,
without needing templates or exact text matches.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor
from transformers.models.qwen2_vl.image_processing_qwen2_vl import smart_resize

from auto_vi.grounding.base import GroundingError, GroundingStrategy

log = logging.getLogger(__name__)

MODEL_NAME = "Hcompany/Holo1.5-3B"

_model = None
_processor = None
_device = None


def _load_model():
    global _model, _processor, _device
    if _model is None:
        log.info("Loading VLM model %s...", MODEL_NAME)
        _processor = AutoProcessor.from_pretrained(MODEL_NAME)

        # Need ~8GB VRAM for inference; fall back to CPU if not enough
        use_gpu = torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 6 * 1024**3
        if use_gpu:
            try:
                _model = AutoModelForImageTextToText.from_pretrained(
                    MODEL_NAME, dtype=torch.bfloat16, device_map="auto",
                )
                _device = _model.device
                log.info("VLM loaded on GPU")
            except Exception:
                log.warning("GPU load failed, falling back to CPU")
                use_gpu = False

        if not use_gpu:
            _model = AutoModelForImageTextToText.from_pretrained(
                MODEL_NAME, dtype=torch.float32,
            )
            _device = torch.device("cpu")
            _model.to(_device)
            log.info("VLM loaded on CPU (slower but stable)")

    return _model, _processor, _device


def _build_prompt() -> str:
    schema = {
        "properties": {
            "action": {"const": "click_absolute", "title": "Action", "type": "string"},
            "x": {"description": "The x coordinate, number of pixels from the left edge.", "title": "X", "type": "integer"},
            "y": {"description": "The y coordinate, number of pixels from the top edge.", "title": "Y", "type": "integer"},
        },
        "required": ["action", "x", "y"],
        "title": "ClickAbsoluteAction",
        "type": "object",
    }
    return (
        "Localize an element on the GUI image according to the provided target "
        "and output a click position.\n"
        f" * You must output a valid JSON following the format: {json.dumps(schema)}\n"
        " Your target is:"
    )


class VLMStrategy(GroundingStrategy):
    name = "vlm"

    def locate(self, image: Image.Image, query: str, cfg: dict[str, Any]) -> tuple[int, int]:
        model, processor, device = _load_model()

        # Resize image per model's image processor config
        ip = processor.image_processor
        rh, rw = smart_resize(
            image.height, image.width,
            factor=ip.patch_size * ip.merge_size,
            min_pixels=ip.min_pixels,
            max_pixels=ip.max_pixels,
        )
        resized = image.resize((rw, rh), Image.Resampling.LANCZOS)

        prompt = _build_prompt()
        task = f"Click on the {query} icon"
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": resized},
                    {"type": "text", "text": f"{prompt}\n{task}"},
                ],
            },
        ]

        text_prompt = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = processor(
            text=[text_prompt], images=[resized], padding=True, return_tensors="pt",
        ).to(device)

        with torch.no_grad():
            generated_ids = model.generate(**inputs, max_new_tokens=128)

        trimmed = [o[len(i):] for i, o in zip(inputs.input_ids, generated_ids)]
        result = processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        log.info("VLM raw output: %s", result)

        try:
            data = json.loads(result)
            rx, ry = int(data["x"]), int(data["y"])
        except (json.JSONDecodeError, KeyError) as e:
            raise GroundingError(f"VLM: failed to parse output: {result!r}") from e

        # Scale coordinates back from resized image to original
        x = int(rx * image.width / rw)
        y = int(ry * image.height / rh)

        log.info("VLM grounded '%s' → resized(%d,%d) → original(%d,%d)", query, rx, ry, x, y)
        return x, y
