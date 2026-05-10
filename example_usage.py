"""
example_usage.py  –  Live webcam demo for gesture_module
=========================================================
Demonstrates both usage patterns:
  Pattern A – zero-config (bundled model, no path needed)
  Pattern B – custom model (user model checked first, bundled as fallback)

Run:
    python example_usage.py

Press  Q  or  ESC  to quit.
"""

import cv2
from mp_gesture_lib import GestureDetector

# ── CONFIG ──────────────────────────────────────────────────────────────────
CAMERA_IDX = 0          # change if your webcam is at a different index
WIDTH, HEIGHT = 1280, 720

# Pattern A: zero-config — bundled model auto-loaded, no path needed
detector = GestureDetector()

# Pattern B: custom model — uncomment to use your own .task file
# User model is checked FIRST; bundled models act as fallback.
# detector = GestureDetector(model_path="Gesture Calculator/operations.task")
# ────────────────────────────────────────────────────────────────────────────


def main() -> None:
    cap = cv2.VideoCapture(CAMERA_IDX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    print("Gesture Module Demo – press Q or ESC to quit")
    print("-" * 45)

    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            print("Camera read failed – exiting.")
            break

        result = detector.detect(frame)   # <── the one call you need

        # ── overlay ─────────────────────────────────────────────────────────
        display = result.annotated_frame if result.annotated_frame is not None else frame

        is_match = result.gesture != "unknown"
        color = (0, 220, 80) if is_match else (0, 100, 255)

        lines = [
            f"Gesture   : {result.gesture}",
            f"Confidence: {result.confidence:.1%}",
            f"Raw label : {result.raw_label}",
        ]
        y = 40
        for line in lines:
            cv2.putText(display, line, (20, y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.85, color, 1, cv2.LINE_AA)
            y += 34
        # ────────────────────────────────────────────────────────────────────

        cv2.imshow("Gesture Module – Demo", display)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
