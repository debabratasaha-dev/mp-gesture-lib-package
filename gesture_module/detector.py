"""
detector.py  –  Core gesture detection engine
==============================================
Wraps MediaPipe GestureRecognizer + rule-based landmark geometry checks
into a single, reusable class.

Detection pipeline (in order — breaks at first match)
------------------------------------------------------
1. User model    – custom .task file supplied by caller (if any)
2. Bundled models– all .task files in gesture_module/models/ (auto-discovered)
3. Rule-based    – two-hand geometry (plus / multiply)
4. Finger count  – counts extended fingers → "1" – "10"
5. "unknown"     – nothing matched

Threshold
---------
Default 0.30 (30 %).  Each ML stage accepts the first gesture whose score
≥ threshold and immediately returns without falling through to the next stage.

Return value
------------
Every public method returns a ``GestureResult`` dataclass:
    gesture    : str   – gesture name, or "unknown" if nothing matched
    confidence : float – probability 0.0 – 1.0
                         Rule-based / finger-count → 1.0
                         ML detections → model score
                         "unknown" → 0.0
    raw_label  : str   – internal label before any mapping (debug)
    annotated_frame : np.ndarray | None – BGR frame with skeleton drawn
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from mediapipe import solutions
from mediapipe.framework.formats import landmark_pb2
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from .registry import get_bundled_model_paths


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
        Examples: "plus", "minus", "multiply", "divide", "equal",
        "clear", "0"–"10", or any label from a custom model, or "unknown".
    confidence : float
        Probability estimate in [0.0, 1.0].
        Rule-based detections return 1.0.
        ML detections return the model score.
        "unknown" returns 0.0.
    raw_label : str
        Internal label before any mapping (useful for debugging).
    annotated_frame : Optional[np.ndarray]
        BGR frame with hand landmarks drawn, or None if draw_landmarks=False.
    """
    gesture: str
    confidence: float
    raw_label: str
    annotated_frame: Optional[np.ndarray] = field(default=None, repr=False)

    def __str__(self) -> str:
        return (
            f"GestureResult(gesture={self.gesture!r}, "
            f"confidence={self.confidence:.2%})"
        )


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# MediaPipe landmark indices for finger tips
_FINGER_TIP_IDS = [4, 8, 12, 16, 20]

# Default ML confidence threshold (70 %)
_DEFAULT_ML_THRESHOLD = 0.70

# MediaPipe returns these labels when no real gesture is matched.
# Must be filtered out — they are NOT gesture detections.
_MEDIAPIPE_NON_GESTURE_LABELS = {"", "None", "none", "Unknown", "unknown"}


# ---------------------------------------------------------------------------
# Internal landmark helpers
# ---------------------------------------------------------------------------

def _is_finger_extended(landmarks, finger_tip_idx: int) -> bool:
    """Return True when a non-thumb finger is extended (tip above PIP joint)."""
    return landmarks[finger_tip_idx].y < landmarks[finger_tip_idx - 2].y


def _is_thumb_extended(landmarks, hand_type: str, thresh: float = 0.035) -> bool:
    """Return True when thumb is extended (logic differs for left vs right hand)."""
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    if hand_type == "Right":
        return (thumb_tip.x - index_tip.x) > thresh
    else:
        return (index_tip.x - thumb_tip.x) > thresh


def _count_extended_fingers(landmarks, hand_type: str) -> int:
    """Count extended fingers on a single hand (0 – 5)."""
    count = 0
    if _is_thumb_extended(landmarks, hand_type):
        count += 1
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


def _build_recognizer(
    model_path: str, num_hands: int
) -> vision.GestureRecognizer:
    """Create a MediaPipe GestureRecognizer from a .task file path."""
    base_options = mp_python.BaseOptions(model_asset_path=model_path)
    options = vision.GestureRecognizerOptions(
        base_options=base_options,
        num_hands=num_hands,
    )
    return vision.GestureRecognizer.create_from_options(options)


def _run_recognizer(
    recognizer: vision.GestureRecognizer,
    mp_img: mp.Image,
    threshold: float,
) -> Optional[tuple[str, float, str]]:
    """
    Run *recognizer* on *mp_img*.

    Returns (gesture_name, confidence, raw_label) for the first gesture
    whose score ≥ threshold AND whose label is a real gesture (not MediaPipe's
    internal 'None' / background class), or None if nothing qualifies.
    """
    result = recognizer.recognize(mp_img)
    if not result.hand_landmarks:
        return None
    for idx in range(len(result.hand_landmarks)):
        top = result.gestures[idx][0]
        label = top.category_name
        # Skip MediaPipe's 'no gesture' / background pseudo-labels
        if label in _MEDIAPIPE_NON_GESTURE_LABELS:
            continue
        if top.score >= threshold:
            return (label, float(top.score), f"ml:{label}")
    return None


# ---------------------------------------------------------------------------
# Main detector class
# ---------------------------------------------------------------------------

class GestureDetector:
    """
    Recognise hand gestures from a single BGR/RGB video frame.

    Parameters
    ----------
    model_path : str | None
        Path to a custom ``.task`` MediaPipe model.
        Pass ``None`` (default) to use only the bundled model(s).
        When provided, this model is queried **first**; if it returns a
        confident result the pipeline stops there.
    num_hands : int
        Maximum number of hands to track simultaneously (default 2).
    ml_threshold : float
        Minimum confidence score [0, 1] for accepting an ML prediction
        (default 0.30).  Applied at every ML stage.
    draw_landmarks : bool
        When True, ``GestureResult.annotated_frame`` contains the input
        frame with hand skeleton drawn.  Set False for performance paths.

    Detection order
    ---------------
    1. Custom user model (if ``model_path`` supplied)
    2. All bundled models (``gesture_module/models/*.task``)
    3. Rule-based two-hand geometry (plus / multiply)
    4. Finger count (numbers 1 – 10)
    5. "unknown"

    Usage
    -----
    ::

        # Zero-config — bundled model loads automatically
        detector = GestureDetector()

        # Custom model — checked first, bundled used as fallback
        detector = GestureDetector(model_path="my_gestures.task")

        cap = cv2.VideoCapture(0)
        while cap.isOpened():
            ok, frame = cap.read()
            result = detector.detect(frame)
            print(result.gesture, result.confidence)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        num_hands: int = 2,
        ml_threshold: float = _DEFAULT_ML_THRESHOLD,
        draw_landmarks: bool = True,
    ) -> None:
        self._ml_threshold = ml_threshold
        self._draw_landmarks = draw_landmarks
        self._num_hands = num_hands

        # Stage 1 – user-supplied custom model (optional)
        self._user_recognizer: Optional[vision.GestureRecognizer] = None
        if model_path is not None:
            model_path = os.path.abspath(model_path)
            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Custom model not found: {model_path}"
                )
            self._user_recognizer = _build_recognizer(model_path, num_hands)

        # Stage 2 – bundled models (auto-discovered from gesture_module/models/)
        self._bundled_recognizers: list[vision.GestureRecognizer] = []
        bundled_paths = get_bundled_model_paths()
        if not bundled_paths:
            warnings.warn(
                "gesture_module: no bundled models found in gesture_module/models/. "
                "Only custom model (if provided) and rule-based detection will work.",
                RuntimeWarning,
                stacklevel=2,
            )
        for path in bundled_paths:
            self._bundled_recognizers.append(
                _build_recognizer(path, num_hands)
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray, input_is_rgb: bool = False) -> GestureResult:
        """
        Detect the dominant hand gesture in *frame*.

        Parameters
        ----------
        frame : np.ndarray
            A single video frame.  BGR by default (as from ``cv2.VideoCapture``).
            Pass ``input_is_rgb=True`` for RGB arrays.
        input_is_rgb : bool
            Set True if *frame* is already in RGB format.

        Returns
        -------
        GestureResult
            Dataclass with ``gesture``, ``confidence``, ``raw_label``,
            and optionally ``annotated_frame``.
        """
        if frame is None or frame.size == 0:
            raise ValueError("Received an empty frame.")

        # Normalise to RGB for MediaPipe
        rgb = frame if input_is_rgb else cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # We need at least one recognizer run to get hand landmarks for drawing.
        # Use user recognizer if present, else first bundled recognizer.
        primary_recognizer = (
            self._user_recognizer
            or (self._bundled_recognizers[0] if self._bundled_recognizers else None)
        )

        # Landmarks are drawn from primary recognition result
        annotated: Optional[np.ndarray] = None
        primary_recognition = None
        if primary_recognizer is not None:
            primary_recognition = primary_recognizer.recognize(mp_img)
            if self._draw_landmarks:
                drawn = _draw_landmarks(mp_img.numpy_view(), primary_recognition)
                annotated = cv2.cvtColor(cv2.flip(drawn, 1), cv2.COLOR_RGB2BGR)

            if not primary_recognition.hand_landmarks:
                return GestureResult(
                    gesture="unknown",
                    confidence=0.0,
                    raw_label="no_hand",
                    annotated_frame=annotated,
                )
        else:
            # No recognizers at all — still try rule/finger checks via a
            # MediaPipe Hands detection? Without a recognizer we can't get
            # landmark data. Warn and return unknown.
            warnings.warn(
                "No recognizers available. Install bundled models or supply model_path.",
                RuntimeWarning,
                stacklevel=2,
            )
            return GestureResult(
                gesture="unknown",
                confidence=0.0,
                raw_label="no_recognizer",
                annotated_frame=annotated,
            )

        return self._classify(mp_img, primary_recognition, annotated)

    # ------------------------------------------------------------------
    # Private classification pipeline
    # ------------------------------------------------------------------

    def _classify(
        self,
        mp_img: mp.Image,
        primary_recognition,
        annotated_frame: Optional[np.ndarray],
    ) -> GestureResult:
        """
        Run the full detection pipeline in priority order.
        Breaks immediately at each stage if a confident result is found.
        """

        # ── Stage 1: User custom model ────────────────────────────────
        if self._user_recognizer is not None:
            hit = _run_recognizer(self._user_recognizer, mp_img, self._ml_threshold)
            if hit is not None:
                gesture, confidence, raw = hit
                return GestureResult(
                    gesture=gesture,
                    confidence=confidence,
                    raw_label=raw,
                    annotated_frame=annotated_frame,
                )

        # ── Stage 2: Bundled models (each in sequence, break on first hit) ──
        for bundled_rec in self._bundled_recognizers:
            hit = _run_recognizer(bundled_rec, mp_img, self._ml_threshold)
            if hit is not None:
                gesture, confidence, raw = hit
                return GestureResult(
                    gesture=gesture,
                    confidence=confidence,
                    raw_label=raw,
                    annotated_frame=annotated_frame,
                )

        # ── Stage 3: Rule-based two-hand gestures ─────────────────────
        rule_result = self._check_two_hand_rules(primary_recognition)
        if rule_result is not None:
            gesture, raw = rule_result
            return GestureResult(
                gesture=gesture,
                confidence=1.0,
                raw_label=raw,
                annotated_frame=annotated_frame,
            )

        # ── Stage 4: Finger count ──────────────────────────────────────
        count_result = self._check_finger_count(primary_recognition)
        if count_result is not None:
            count, raw = count_result
            return GestureResult(
                gesture=str(count),
                confidence=1.0,
                raw_label=raw,
                annotated_frame=annotated_frame,
            )

        # ── Stage 5: Nothing matched ───────────────────────────────────
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

        right = hand_data["Right"]
        left  = hand_data["Left"]

        required = ("tip", "pip")
        if not (all(k in right for k in required) and all(k in left for k in required)):
            return None
        if not all(v is not None for v in (right["tip"], left["tip"],
                                           right["pip"], left["pip"])):
            return None

        # plus: right tip notably above left tip; pips horizontally close
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

    def _check_finger_count(self, recognition) -> Optional[tuple[int, str]]:
        """
        Count extended fingers across all detected hands (1 – 10).

        Returns (count, raw_label) or None if no fingers are extended.
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
