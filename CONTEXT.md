# CONTEXT.md — mp_gesture_lib Project Context for AI Agent

> This file gives any AI model or contributor the full context of this project in one read.

---

## 1. What This Project Is

**mp_gesture_lib** is a reusable, plug-and-play Python gesture recognition module extracted from a hand-gesture-based calculator project. It wraps MediaPipe's GestureRecognizer and custom landmark geometry rules into a single importable package. The goal: any developer can detect hand gestures from a webcam frame with **one function call**, no CV expertise required.

---

## 2. Origin Project

The module was extracted from **`Gesture Calculator/`** — a Python app that lets users perform arithmetic (+, -, *, /, =, clear) using only hand gestures and a webcam. That original project used:
- `app.py` — monolithic script mixing gesture logic + UI + calculator loop
- `calculate.py` — arithmetic expression evaluator
- `operations.task` — custom-trained MediaPipe GestureRecognizer model

The gesture logic was **extracted and modularised** into `mp_gesture_lib/`.

---

## 3. Repository Structure

```
mp-gesture-lib-package/                     ← repo root
├── mp_gesture_lib/                 ← THE MODULE (importable package)
│   ├── __init__.py                 ← public API: exports GestureDetector, GestureResult
│   ├── detector.py                 ← all detection logic (core engine)
│   ├── registry.py                 ← auto-discovers *.task models in models/
│   └── models/
│       ├── __init__.py             ← makes models/ a sub-package (importlib.resources)
│       └── operations.task         ← bundled ML model (MediaPipe GestureRecognizer)
├── example_usage.py                ← live webcam demo
├── requirements.txt                ← mediapipe, opencv-python, numpy
├── LICENSE.txt   
└── README.md
```

---

## 4. Public API

### Import
```python
from mp_gesture_lib import GestureDetector, GestureResult
```

### `GestureDetector` constructor
```python
GestureDetector(
    model_path: str | None = None,   # path to custom .task file; None = use bundled
    num_hands: int = 2,              # max hands to track
    ml_threshold: float = 0.70,      # min confidence to accept ML prediction
    draw_landmarks: bool = True,     # draw skeleton on annotated_frame
)
```

### `detector.detect(frame, input_is_rgb=False) → GestureResult`
- `frame`: BGR numpy array (from `cv2.VideoCapture`) by default
- Returns `GestureResult` dataclass

### `GestureResult` fields
| Field | Type | Description |
|-------|------|-------------|
| `gesture` | `str` | Gesture name or `"unknown"` |
| `confidence` | `float` | 0.0–1.0 (1.0 for rule-based, model score for ML, 0.0 for unknown) |
| `raw_label` | `str` | Internal debug label (e.g. `"ml:minus"`, `"rule:plus"`, `"rule:fingers:3"`) |
| `annotated_frame` | `np.ndarray \| None` | BGR frame with hand skeleton drawn |

---

## 5. Detection Pipeline (Priority Order)

Breaks immediately at first confident match:

```
1. User custom model   → model_path arg; any label ≥ threshold → return immediately
2. Bundled model(s)    → all *.task in mp_gesture_lib/models/; break on first hit
3. Rule-based (2 hands)→ geometry checks for "plus" and "multiply"
4. Finger count        → counts extended fingers → "1"–"10"
5. "unknown"           → nothing matched, confidence = 0.0
```

**Threshold default: 0.70.** MediaPipe's internal `""` / `"None"` labels (background class) are filtered out and never returned as a gesture.

---

## 6. Gesture Support

| Gesture | Method | Return value |
|---------|--------|-------------|
| Numbers 1–10 | Finger-count geometry | `"1"` – `"10"` |
| Zero | ML model | `"0"` |
| Plus | Two-hand geometry rule | `"plus"` |
| Multiply | Two-hand geometry rule | `"multiply"` |
| Minus | ML model | `"minus"` |
| Divide | ML model | `"divide"` |
| Equal | ML model | `"equal"` |
| Clear | ML model | `"clear"` |
| Nothing / unrecognised | — | `"unknown"` |

### Two-hand rules (geometry)
- **plus**: right index tip notably above left index tip; both PIP joints horizontally close (< 0.04 normalised units)
- **multiply**: right index tip x > left index tip x AND roughly same y-coordinate

### Finger count
- Thumb: direction-aware (right hand: `thumb.x - index.x > 0.035`; left hand: opposite)
- Other fingers: tip.y < PIP.y = extended

---

## 7. Multi-Model Architecture

**Bundled models** (for package developers):
- Drop any `.task` file into `mp_gesture_lib/models/`
- `registry.py` auto-discovers all `*.task` files via `importlib.resources`
- All bundled models load at init; each queried in sequence during detection
- Zero code change needed — works after `pip install` too

**Custom user model** (for end users):
```python
detector = GestureDetector(model_path="my_custom.task")
```
- Queried **first** (highest priority)
- Bundled models used as fallback if user model returns nothing above threshold
- Any label from user model passes through raw (no hard-coded mapping)

---

## 8. Key Design Decisions

| Decision | Reason |
|----------|--------|
| `model_path` optional (default `None`) | Zero-config UX; bundled model just works |
| Labels pass through raw (no mapping dict) | Supports any custom model out of the box |
| Filter `""` / `"None"` MP labels | MediaPipe returns background class with high confidence; must skip |
| Rule-based AFTER ML models | ML operations (minus, divide, etc.) run first; rules only for gestures models can't handle |
| `confidence=1.0` for rule-based | Geometry rules are deterministic; no probability to report |
| `draw_landmarks` flag | Performance paths (robotics, embedded) skip expensive drawing |
| `importlib.resources` for model path | Works both in dev and after `pip install` (zip-safe) |

---

## 9. Known Limitation

**1-finger = "minus" conflict**: The bundled `operations.task` model was trained with 1-finger-pointing = `"minus"`. Finger count rule also produces `"1"` for 1 finger. Since ML runs before finger count, model wins → shows `"minus"` not `"1"`. Fix requires retraining the model to use a visually distinct gesture for "minus".

---

## 10. Usage Examples

### Minimal (zero-config)
```python
import cv2
from mp_gesture_lib import GestureDetector

detector = GestureDetector()
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ok, frame = cap.read()
    result = detector.detect(frame)
    print(result.gesture, result.confidence)  # "plus" 1.0 / "3" 1.0 / "minus" 0.91
```

### With custom model (user model takes priority)
```python
detector = GestureDetector(
    model_path="my_custom_gestures.task",
    ml_threshold=0.80,
    draw_landmarks=False,   # faster, no skeleton drawing
)
```

### RGB input (e.g. from PIL / torchvision)
```python
result = detector.detect(rgb_frame, input_is_rgb=True)
```

---

## 11. Dependencies

```
mediapipe          # hand tracking + gesture recognition
opencv-python      # image/video processing
numpy              # array operations
Python 3.8–3.12    # mediapipe does NOT support 3.13+
```

---

## 12. Documentation & Deployment

The project includes a static, beautifully designed documentation website located in the `documentation/` folder.

- **Design Features**: Dark mode default, glassmorphism UI, code syntax highlighting (PrismJS - VSCode Dark+ style), interactive tabs, and a dedicated searchable gesture directory.
- **Pages**:
  - `index.html`: Hero section, features, gesture grid, code examples, API reference.
  - `gestures.html`: A dedicated search page to filter and find specific gestures or supported operations dynamically.
- **Deployment**: The website can be directly hosted on GitHub Pages (e.g. `https://debabratasaha-dev.github.io/mp-gesture-lib-package`). The `pyproject.toml` URLs are configured to point to this documentation site.

---

## 13. To-Do / Future Work

- [x] Create project documentation website
- [x] Configure PyPI metadata and package data in `pyproject.toml`
- [ ] Publish to PyPI as `mp-gesture-lib`
- [ ] Resolve 1-finger vs "minus" conflict by retraining model
- [ ] Add async/callback mode for streaming pipelines
- [ ] Unit tests
