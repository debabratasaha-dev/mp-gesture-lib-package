"""
detector.py  –  Core gesture detection engine
==============================================
Wraps MediaPipe GestureRecognizer + rule-based landmark geometry checks
into a single, reusable class.

Detected gestures
-----------------
Numeric  : "0" – "10"   (finger-count via landmark geometry, "0" also via ML)
Operation: "plus"        (two-hand rule: right index above left index, pips close)
           "multiply"    (two-hand rule: right index x > left index x, roughly same y)
           "minus"       (ML model)
           "divide"      (ML model)
           "equal"       (ML model)
           "clear"       (ML model)

Return value
------------
Every public method returns a ``GestureResult`` named-tuple:
    gesture    : str   – gesture name, or "unknown" if nothing matched
    confidence : float – probability 0.0–1.0  (1.0 for rule-based detections,
                         model score for ML detections, 0.0 for "unknown")
    raw_label  : str   – internal label before any name-mapping (debug use)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision


# ---------------------------------------------------------------------------
# Public result type
# ---------------------------------------------------------------------------

@dataclass
class GestureResult:
    """
    Returned by every detection call.

    Attributes
    ----------
    gesture : str
        Human-readable gesture name.
        One of: "0"–"10", "plus", "minus", "multiply", "divide", "equal",
        "clear", "unknown".
    confidence : float
        Probability estimate in [0.0, 1.0].
        Rule-based detections always return 1.0.
        ML detections return the model's top-gesture score.
        "unknown" always returns 0.0.
    raw_label : str
        Internal label before mapping (useful for debugging).
    annotated_frame : Optional[np.ndarray]
        BGR frame with hand landmarks drawn, or *None* if drawing was
        disabled (``draw_landmarks=False`` in constructor).
    """
    gesture: str
    confidence: float
    raw_label: str
    annotated_frame: Optional[np.ndarray] = field(default=None, repr=False)

    def __str__(self) -> str:
        return f"GestureResult(gesture={self.gesture!r}, confidence={self.confidence:.2%})"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

# MediaPipe landmark indices for finger tips and their PIP joints
_FINGER_TIP_IDS = [4, 8, 12, 16, 20]

# ML label → canonical gesture name
_ML_LABEL_MAP: dict[str, str] = {
    "0":      "0",
    "clear":  "clear",
    "equal":  "equal",
    "minus":  "minus",
    "devide": "divide",   # typo intentional – matches the model's trained label
    "divide": "divide",
}

# Minimum ML model score to trust a prediction
_DEFAULT_ML_THRESHOLD = 0.77


def _is_finger_extended(landmarks, finger_tip_idx: int) -> bool:
    """Return True when a non-thumb finger is extended (tip above PIP)."""
    return landmarks[finger_tip_idx].y < landmarks[finger_tip_idx - 2].y


def _is_thumb_extended(landmarks, hand_type: str, thresh: float = 0.035) -> bool:
    """Return True when thumb is extended (rule differs for left/right hand)."""
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    if hand_type == "Right":
        return (thumb_tip.x - index_tip.x) > thresh
    else:  # Left
        return (index_tip.x - thumb_tip.x) > thresh


def _count_extended_fingers(landmarks, hand_type: str) -> int:
    """Count extended fingers on a single hand (0–5)."""
    count = 0
    # thumb
    if _is_thumb_extended(landmarks, hand_type):
        count += 1
    # index → pinky
    for tip_id in _FINGER_TIP_IDS[1:]:
        if _is_finger_extended(landmarks, tip_id):
            count += 1
    return count


def _draw_landmarks(rgb_image: np.ndarray, result) -> np.ndarray:
    """Draw hand landmarks on *rgb_image* and return annotated copy (RGB)."""
    annotated = np.copy(rgb_image)
    for hand_landmarks in result.hand_landmarks:
        proto = landmark_pb2.NormalizedLandmarkList()
        proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=lm.x, y=lm.y, z=lm.z)
            for lm in hand_landmarks
        ])
        solutions.drawing_utils.draw_landmarks(
            annotated,
            proto,
            solutions.hands.HAND_CONNECTIONS,
            solutions.drawing_styles.get_default_hand_landmarks_style(),
            solutions.drawing_styles.get_default_hand_connections_style(),
        )
    return annotated


# ---------------------------------------------------------------------------
# Main detector class
# ---------------------------------------------------------------------------

class GestureDetector:
    """
    Recognise hand gestures from a single BGR/RGB video frame.

    Parameters
    ----------
    model_path : str
        Absolute or relative path to the ``operations.task`` MediaPipe model.
    num_hands : int
        Maximum number of hands to track simultaneously (default 2).
    ml_threshold : float
        Minimum confidence score [0, 1] for accepting an ML prediction
        (default 0.77).  Lower → more sensitive but more noisy.
    draw_landmarks : bool
        When True, ``GestureResult.annotated_frame`` contains the input frame
        with hand skeleton drawn.  Set False for performance-critical paths.

    Usage
    -----
    ::

        detector = GestureDetector("Gesture Calculator/operations.task")

        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break
            result = detector.detect(frame)
            print(result)
    """

    def __init__(
        self,
        model_path: str,
        num_hands: int = 2,
        ml_threshold: float = _DEFAULT_ML_THRESHOLD,
        draw_landmarks: bool = True,
    ) -> None:
        model_path = os.path.abspath(model_path)
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"MediaPipe model not found: {model_path}\n"
                "Download or copy 'operations.task' into your project directory."
            )

        base_options = mp_python.BaseOptions(model_asset_path=model_path)
        options = vision.GestureRecognizerOptions(
            base_options=base_options,
            num_hands=num_hands,
        )
        self._recognizer = vision.GestureRecognizer.create_from_options(options)
        self._ml_threshold = ml_threshold
        self._draw_landmarks = draw_landmarks

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray, input_is_rgb: bool = False) -> GestureResult:
        """
        Detect the dominant hand gesture in *frame*.

        Parameters
        ----------
        frame : np.ndarray
            A single video frame.  By default expected in **BGR** format
            (as returned by ``cv2.VideoCapture``).  Pass ``input_is_rgb=True``
            if you supply an RGB array.
        input_is_rgb : bool
            Set True if ``frame`` is already RGB.

        Returns
        -------
        GestureResult
            Named-tuple with ``gesture``, ``confidence``, ``raw_label``,
            and optionally ``annotated_frame``.
        """
        if frame is None or frame.size == 0:
            raise ValueError("Received empty frame.")

        # Normalise to RGB for MediaPipe
        rgb = frame if input_is_rgb else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        recognition = self._recognizer.recognize(mp_img)

        # Draw landmarks on a horizontally-flipped copy (mirror view)
        annotated: Optional[np.ndarray] = None
        if self._draw_landmarks:
            drawn = _draw_landmarks(mp_img.numpy_view(), recognition)
            annotated = cv2.cvtColor(cv2.flip(drawn, 1), cv2.COLOR_RGB2BGR)

        if not recognition.hand_landmarks:
            return GestureResult(
                gesture="unknown",
                confidence=0.0,
                raw_label="no_hand",
                annotated_frame=annotated,
            )

        return self._classify(recognition, annotated)

    # ------------------------------------------------------------------
    # Private classification pipeline
    # ------------------------------------------------------------------

    def _classify(self, recognition, annotated_frame) -> GestureResult:
        """Run the full three-step classification pipeline."""

        # Step 1 – two-hand rule-based checks (plus / multiply)
        rule_result = self._check_two_hand_rules(recognition)
        if rule_result is not None:
            gesture, raw = rule_result
            return GestureResult(
                gesture=gesture,
                confidence=1.0,
                raw_label=raw,
                annotated_frame=annotated_frame,
            )

        # Step 2 – ML model predictions (operations)
        ml_result = self._check_ml_gestures(recognition)
        if ml_result is not None:
            gesture, confidence, raw = ml_result
            return GestureResult(
                gesture=gesture,
                confidence=confidence,
                raw_label=raw,
                annotated_frame=annotated_frame,
            )

        # Step 3 – finger-count (numbers 1–10)
        count_result = self._check_finger_count(recognition)
        if count_result is not None:
            count, raw = count_result
            return GestureResult(
                gesture=str(count),
                confidence=1.0,
                raw_label=raw,
                annotated_frame=annotated_frame,
            )

        # Nothing matched
        return GestureResult(
            gesture="unknown",
            confidence=0.0,
            raw_label="no_match",
            annotated_frame=annotated_frame,
        )

    def _check_two_hand_rules(self, recognition) -> Optional[tuple[str, str]]:
        """
        Rule-based two-hand gesture detection.

        Returns (gesture_name, raw_label) or None.

        plus     – right index-tip significantly above left index-tip;
                   both PIPs horizontally close (< 0.04 normalised units).
        multiply – right index-tip x > left index-tip x AND roughly same y.
        """
        hand_data: dict[str, dict] = {"Right": {}, "Left": {}}

        for hand_landmarks, hand in zip(
            recognition.hand_landmarks, recognition.handedness
        ):
            hand_type = hand[0].category_name
            hand_data[hand_type]["tip"] = hand_landmarks[8]   # index tip
            hand_data[hand_type]["pip"] = hand_landmarks[6]   # index PIP
            hand_data[hand_type]["dip"] = hand_landmarks[7]   # index DIP

        right = hand_data["Right"]
        left  = hand_data["Left"]

        # Both hands must be visible
        required = ("tip", "pip", "dip")
        if not (all(k in right for k in required) and all(k in left for k in required)):
            return None
        if not all(v is not None for v in (right["tip"], left["tip"], right["pip"], left["pip"])):
            return None

        # plus: right tip notably above left tip; pips horizontally aligned
        if (
            (right["tip"].y + 0.052) < left["tip"].y
            and abs(left["pip"].x - right["pip"].x) < 0.04
        ):
            return ("plus", "rule:plus")

        # multiply: right tip to the right of left tip; roughly same height
        if (
            right["tip"].x > left["tip"].x
            and right["tip"].y > (left["tip"].y - 0.01)
        ):
            return ("multiply", "rule:multiply")

        return None

    def _check_ml_gestures(self, recognition) -> Optional[tuple[str, float, str]]:
        """
        Check ML model predictions for operation gestures.

        Returns (gesture_name, confidence, raw_label) or None.
        """
        for idx in range(len(recognition.hand_landmarks)):
            top = recognition.gestures[idx][0]
            if top.score >= self._ml_threshold:
                raw_label = top.category_name
                mapped = _ML_LABEL_MAP.get(raw_label)
                if mapped is not None:
                    return (mapped, float(top.score), f"ml:{raw_label}")
        return None

    def _check_finger_count(self, recognition) -> Optional[tuple[int, str]]:
        """
        Count extended fingers across all detected hands (1–10).

        Returns (count, raw_label) or None if no fingers extended.
        """
        total = 0
        for hand_landmarks, hand in zip(
            recognition.hand_landmarks, recognition.handedness
        ):
            hand_type = hand[0].category_name
            total += _count_extended_fingers(hand_landmarks, hand_type)

        if total > 0:
            return (total, f"rule:fingers:{total}")
        return None
