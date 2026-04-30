"""Download and cache Holo1.5-3B model + processor for VLM grounding."""

import subprocess
import sys

# Install dependencies if missing
subprocess.check_call(["uv", "pip", "install", "pydantic", "hf_xet", "transformers>=4.54.0,<4.57.0"])

MODEL = "Hcompany/Holo1.5-3B"

print(f"Downloading processor for {MODEL}...")
from transformers import AutoProcessor
processor = AutoProcessor.from_pretrained(MODEL)
print("Processor cached.")

print(f"Downloading model {MODEL} (this may take a while)...")
from transformers import AutoModelForImageTextToText
import torch
model = AutoModelForImageTextToText.from_pretrained(
    MODEL,
    torch_dtype=torch.bfloat16,
)
print(f"Model cached. Total params: {sum(p.numel() for p in model.parameters()) / 1e9:.1f}B")
print("Done! The model is now cached in your HuggingFace cache directory.")
