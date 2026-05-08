"""
gesture_module
==============
A plug-and-play gesture recognition module built on MediaPipe and OpenCV.

Quick-start
-----------
    from gesture_module import GestureDetector

    detector = GestureDetector(model_path="path/to/operations.task")

    result = detector.detect(frame)          # pass a BGR numpy frame
    print(result.gesture, result.confidence) # e.g.  "plus"  0.93

    # Or use the one-shot helper that opens the webcam for you:
    # detector.run_demo()
"""

from .detector import GestureDetector, GestureResult

__all__ = ["GestureDetector", "GestureResult"]
__version__ = "1.0.0"
