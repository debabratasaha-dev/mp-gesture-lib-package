# MP-Gesture-Lib

A plug-and-play **hand gesture recognition module** built on MediaPipe and OpenCV.  
Detect gesture names + confidence from a webcam frame in **one function call**.

📖 **[Full Documentation →](https://debabratasaha-dev.github.io/mp-gesture-lib-package)**

---

## Install

```bash
pip install mp-gesture-lib
```

> Requires Python >= 3.8 Bundled model included — no external files needed. (check `mediapipe` support for your python version)

---

## Quick Start

```python
import cv2
from mp_gesture_lib import GestureDetector

detector = GestureDetector()  # zero-config

cap = cv2.VideoCapture(0)
while cap.isOpened():
    ok, frame = cap.read()
    result = detector.detect(frame)

    print(result.gesture)     # "plus", "3", "minus", "unknown" …
    print(result.confidence)  # 0.0 – 1.0

    cv2.imshow("Gestures", result.annotated_frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
```

---

## Supported Gestures

| Gesture | Returns |
|---------|---------|
| Numbers 1 – 10 | `"1"` – `"10"` |
| Arithmetic ops | `"plus"` `"minus"` `"multiply"` `"divide"` |
| Calculator | `"equal"` `"clear"` `"0"` |
| Nothing / unrecognised | `"unknown"` |

---

## Custom Model

```python
# Your model checked first — bundled used as fallback
detector = GestureDetector(model_path="my_gestures.task")
```

---

## Acknowledgements

- [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/guide) — hand tracking & gesture recognition
- [OpenCV](https://opencv.org/) — image & video processing

---

## License

MIT © [Debabrata Saha](https://github.com/debabratasaha-dev)  
See [LICENSE](./LICENSE.txt) for details.