# auto-vi — Vision-Based Desktop Automation with Dynamic Icon Grounding

Locates desktop icons using computer vision and automates Notepad to save blog posts fetched from JSONPlaceholder.

## Setup

```bash
uv sync
```

### Optional: GPU acceleration

For faster OCR with an NVIDIA GPU, install CUDA-enabled PyTorch after syncing:

```bash
uv pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121 --reinstall
```

Then run with `.venv\Scripts\python.exe -m auto_vi` instead of `uv run auto-vi` to avoid uv overwriting the CUDA torch.

## Usage

```bash
auto-vi
# or with verbose logging
auto-vi -v
```

## How It Works

1. Kills any lingering Notepad instances and minimizes all windows
2. Takes a screenshot of the desktop
3. Locates the Notepad icon using the configured grounding strategies (in order)
4. Double-clicks the icon to launch Notepad
5. For each of the first N posts from JSONPlaceholder:
   - Types the post content (`Title: {title}\n\n{body}`)
   - Saves as `post_{id}.txt` to `~/Desktop/tjm-project/`
   - Closes Notepad and repeats from step 1

## Grounding Strategies

Strategies are tried in order (configured in `config.toml`). First success wins.

| Strategy | Method | Speed | Robustness |
|----------|--------|-------|------------|
| `template` | OpenCV multi-scale template matching | Fast | Breaks on theme/icon-size changes |
| `ocr` | EasyOCR text detection | Slower | Position-agnostic, needs readable label |

### Template Matching

Uses `cv2.matchTemplate` with multi-scale search (0.8×–1.2×). Templates are extracted from the system at multiple sizes and stored in `templates/`.

### OCR

Scans the screenshot for text, exact-matches the query (e.g. "Notepad"), and returns the coordinates above the label (where the icon sits).

## Project Structure

```
auto_vi/
├── core/
│   ├── automation.py   # Mouse/keyboard helpers (pyautogui + pywinauto)
│   ├── capture.py      # Screenshot capture (mss)
│   ├── cli.py          # CLI entry point
│   └── config.py       # TOML config loader
├── grounding/
│   ├── base.py         # Abstract GroundingStrategy
│   ├── registry.py     # Strategy registry, tries in order
│   ├── ocr.py          # EasyOCR strategy
│   └── template.py     # OpenCV template matching strategy
├── workflow/
│   └── orchestrator.py # Main automation loop
templates/              # Icon templates extracted from system
config.toml             # All configuration
```

## Configuration

All settings are in `config.toml`. Key options:

- `[workflow]` — API URL, post count, output directory, target icon name
- `[grounding]` — Strategy order, per-strategy thresholds and parameters
- `[retry]` — Max attempts, delay between retries, window detection timeout
- `[display]` — Monitor selection and resolution

## TODO

- [x] Core: Make it work
- [x] Improve: Add grounding methods (template matching)
- [x] Improve: Add robust error handling
- [ ] Improve: Add more grounding methods (vision-language model)
