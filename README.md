# auto-vi — Vision-Based Desktop Automation with Dynamic Icon Grounding

Locates desktop icons using computer vision and automates Notepad to save blog posts fetched from JSONPlaceholder.

## Setup

```bash
uv sync
```

### Optional: GPU acceleration

For faster OCR with an NVIDIA GPU, install CUDA-enabled PyTorch:

```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## Usage

```bash
auto-vi
```

## TODO
- [x] Core: Make it work
- [ ] Improve: Add grounding methods
- [ ] Improve: Add robust error handling