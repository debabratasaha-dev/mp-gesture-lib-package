"""
example_usage.py  –  Live webcam demo for gesture_module
=========================================================
Run:
    python example_usage.py

Press  Q  or  ESC  to quit.
"""

import cv2
from gesture_module import GestureDetector

# ── CONFIG ──────────────────────────────────────────────────────────────────
MODEL_PATH  = "Gesture Calculator/operations.task"   # adjust if needed
CAMERA_IDX  = 0        # change if your webcam is at a different index
WIDTH, HEIGHT = 1280, 720
# ────────────────────────────────────────────────────────────────────────────

def main() -> None:
    detector = GestureDetector(
        model_path=MODEL_PATH,
        num_hands=2,
        ml_threshold=0.77,
        draw_landmarks=True,
    )

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

        result = detector.detect(frame)   # <── THE ONE CALL

        # ── overlay ─────────────────────────────────────────────────────────
        display = result.annotated_frame if result.annotated_frame is not None else frame

        label_text  = f"Gesture   : {result.gesture}"
        conf_text   = f"Confidence: {result.confidence:.1%}"
        raw_text    = f"Raw label : {result.raw_label}"

        y = 40
        for line in (label_text, conf_text, raw_text):
            cv2.putText(
                display, line, (20, y),
                cv2.FONT_HERSHEY_DUPLEX, 0.85,
                (0, 255, 0) if result.gesture != "unknown" else (0, 100, 255),
                1, cv2.LINE_AA,
            )
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
