# gesture_module

A plug-and-play **hand gesture recognition module** built on [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) and OpenCV.  
Drop it into any project and get gesture names + confidence scores from a webcam frame in **one function call**.

---

## Supported Gestures

| Gesture | Detection method | `gesture` value |
|---------|-----------------|-----------------|
| Numbers 1–10 | Finger-count (landmark geometry) | `"1"` – `"10"` |
| Zero | ML model | `"0"` |
| Plus / Addition | Two-hand rule (index tip positions) | `"plus"` |
| Multiply | Two-hand rule (index tip positions) | `"multiply"` |
| Minus | ML model | `"minus"` |
| Divide | ML model | `"divide"` |
| Equal | ML model | `"equal"` |
| Clear | ML model | `"clear"` |
| Nothing / unrecognised | — | `"unknown"` |

---

## Requirements

- Python 3.8 – 3.12  _(MediaPipe does **not** support 3.13+)_
- Webcam (for live demos)

---

## Installation

```bash
# 1. Clone / copy this folder into your project
git clone https://github.com/your-org/gesture-module.git

# 2. Install dependencies
pip install -r requirements.txt
```

> **Model file** – place `operations.task` where your code can reach it  
> (default: `Gesture Calculator/operations.task` relative to project root).

---

## Quick Start

```python
import cv2
from gesture_module import GestureDetector

# Initialise once
detector = GestureDetector(model_path="Gesture Calculator/operations.task")

cap = cv2.VideoCapture(0)
while cap.isOpened():
    ok, frame = cap.read()
    if not ok:
        break

    result = detector.detect(frame)          # ← one call

    print(result.gesture)      # e.g. "plus", "3", "unknown"
    print(result.confidence)   # e.g. 0.93  (0.0–1.0)

    if result.annotated_frame is not None:
        cv2.imshow("Gestures", result.annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

Run the bundled demo:

```bash
python example_usage.py
```

---

## API Reference

### `GestureDetector(model_path, num_hands=2, ml_threshold=0.77, draw_landmarks=True)`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_path` | `str` | — | Path to `operations.task` |
| `num_hands` | `int` | `2` | Max hands to track |
| `ml_threshold` | `float` | `0.77` | Min ML confidence to accept |
| `draw_landmarks` | `bool` | `True` | Draw skeleton on output frame |

### `detector.detect(frame, input_is_rgb=False) → GestureResult`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frame` | `np.ndarray` | — | Video frame (BGR by default) |
| `input_is_rgb` | `bool` | `False` | Set `True` for RGB input |

### `GestureResult` (dataclass)

| Field | Type | Description |
|-------|------|-------------|
| `gesture` | `str` | Recognised gesture name or `"unknown"` |
| `confidence` | `float` | Score 0.0 – 1.0 (1.0 for rule-based, 0.0 for unknown) |
| `raw_label` | `str` | Internal label (debug) |
| `annotated_frame` | `np.ndarray \| None` | BGR frame with landmarks drawn |

---

## Project Structure

```
Gesture_Module/
├── gesture_module/
│   ├── __init__.py      # Public API: GestureDetector, GestureResult
│   └── detector.py      # Detection engine
├── Gesture Calculator/
│   ├── app.py           # Original calculator application
│   ├── operations.task  # MediaPipe gesture model
│   └── ...
├── example_usage.py     # Webcam demo
├── requirements.txt
└── README.md
```

---

## How Detection Works

```
Frame (BGR)
    │
    ▼
MediaPipe GestureRecognizer
    │
    ├─ Two hands visible? ──► Rule check (plus / multiply)
    │
    ├─ ML model score ≥ threshold? ──► (0, minus, divide, equal, clear)
    │
    ├─ Count extended fingers ──► "1" – "10"
    │
    └─ Nothing matched ──► "unknown"  (confidence = 0.0)
```

---

## Acknowledgements

- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) – hand tracking & gesture recognition  
- [OpenCV](https://opencv.org/) – image & video processing
