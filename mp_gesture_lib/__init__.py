"""
gesture_module
==============
A plug-and-play gesture recognition module built on MediaPipe and OpenCV.

Quick-start
-----------
    from gesture_module import GestureDetector

    # Zero-config: bundled model loads automatically
    detector = GestureDetector()

    # Or supply your own custom model (checked first, bundled used as fallback)
    detector = GestureDetector(model_path="my_gestures.task")

    result = detector.detect(frame)          # pass a BGR numpy frame
    print(result.gesture, result.confidence) # e.g. "plus"  0.93
"""

from .detector import GestureDetector, GestureResult

__all__ = ["GestureDetector", "GestureResult"]
__version__ = "1.0.0"
