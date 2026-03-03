"""MediaPipe-based hand gesture detector."""

import enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

try:
    import cv2
    import mediapipe as mp
    import numpy as np
    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False

from gesture_control.config import Config


class GestureType(enum.Enum):
    """Enumeration of supported gesture types."""

    NONE = "none"
    PINCH = "pinch"
    THUMBS_UP = "thumbs_up"
    PEACE_SIGN = "peace_sign"
    FIST = "fist"
    OPEN_PALM = "open_palm"
    OK_SIGN = "ok_sign"
    POINTING_UP = "pointing_up"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"


@dataclass
class GestureResult:
    """Result of a single gesture detection pass."""

    gesture: GestureType = GestureType.NONE
    confidence: float = 0.0
    landmarks: List = field(default_factory=list)
    hand_center: Tuple[float, float] = (0.0, 0.0)


class GestureDetector:
    """Detects hand gestures from camera frames using MediaPipe Hands."""

    # MediaPipe landmark indices
    _WRIST = 0
    _THUMB_CMC = 1
    _THUMB_MCP = 2
    _THUMB_IP = 3
    _THUMB_TIP = 4
    _INDEX_MCP = 5
    _INDEX_PIP = 6
    _INDEX_DIP = 7
    _INDEX_TIP = 8
    _MIDDLE_MCP = 9
    _MIDDLE_PIP = 10
    _MIDDLE_DIP = 11
    _MIDDLE_TIP = 12
    _RING_MCP = 13
    _RING_PIP = 14
    _RING_DIP = 15
    _RING_TIP = 16
    _PINKY_MCP = 17
    _PINKY_PIP = 18
    _PINKY_DIP = 19
    _PINKY_TIP = 20

    def __init__(self, config: Config) -> None:
        self._config = config
        self._hands = None
        self._mp_hands = None
        self._mp_drawing = None
        self._mp_drawing_styles = None

        if _MEDIAPIPE_AVAILABLE:
            self._mp_hands = mp.solutions.hands  # type: ignore[attr-defined]
            self._mp_drawing = mp.solutions.drawing_utils  # type: ignore[attr-defined]
            self._mp_drawing_styles = mp.solutions.drawing_styles  # type: ignore[attr-defined]
            self._hands = self._mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=config.min_detection_confidence,
                min_tracking_confidence=config.min_tracking_confidence,
            )

    def process_frame(self, frame) -> Tuple:
        """Process a BGR frame and return (annotated_frame, GestureResult).

        When MediaPipe is unavailable the original frame is returned alongside
        a default GestureResult(NONE).
        """
        result = GestureResult()

        if not _MEDIAPIPE_AVAILABLE or self._hands is None:
            return frame, result

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        detection = self._hands.process(rgb)
        rgb.flags.writeable = True
        annotated = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        if detection.multi_hand_landmarks:
            hand_landmarks = detection.multi_hand_landmarks[0]
            handedness = (
                detection.multi_handedness[0].classification[0].label
                if detection.multi_handedness
                else "Right"
            )

            # Draw landmarks
            self._mp_drawing.draw_landmarks(
                annotated,
                hand_landmarks,
                self._mp_hands.HAND_CONNECTIONS,
                self._mp_drawing_styles.get_default_hand_landmarks_style(),
                self._mp_drawing_styles.get_default_hand_connections_style(),
            )

            lm_list = [
                (lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark
            ]
            gesture_type = self._detect_gesture(lm_list, handedness)
            confidence = self._calculate_confidence(lm_list)
            hand_center = self._get_hand_center(lm_list)

            result = GestureResult(
                gesture=gesture_type,
                confidence=confidence,
                landmarks=lm_list,
                hand_center=hand_center,
            )

            # Overlay gesture label
            label = gesture_type.value.replace("_", " ").upper()
            conf_pct = int(confidence * 100)
            cv2.putText(
                annotated,
                f"{label}  {conf_pct}%",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )

        return annotated, result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_gesture(self, landmarks: list, handedness: str) -> GestureType:
        """Determine the gesture type from normalised landmark coordinates."""
        thumb_up = self._is_finger_up(landmarks, self._THUMB_TIP, self._THUMB_IP)
        index_up = self._is_finger_up(landmarks, self._INDEX_TIP, self._INDEX_PIP)
        middle_up = self._is_finger_up(landmarks, self._MIDDLE_TIP, self._MIDDLE_PIP)
        ring_up = self._is_finger_up(landmarks, self._RING_TIP, self._RING_PIP)
        pinky_up = self._is_finger_up(landmarks, self._PINKY_TIP, self._PINKY_PIP)

        fingers_up = [thumb_up, index_up, middle_up, ring_up, pinky_up]
        extended_count = sum(fingers_up)

        # PINCH – thumb tip very close to index tip
        pinch_dist = self._calculate_distance(
            landmarks[self._THUMB_TIP], landmarks[self._INDEX_TIP]
        )
        if pinch_dist < 0.05:
            return GestureType.PINCH

        # OK_SIGN – thumb + index close (moderate distance), other fingers extended
        ok_dist = self._calculate_distance(
            landmarks[self._THUMB_TIP], landmarks[self._INDEX_TIP]
        )
        if ok_dist < 0.10 and middle_up and ring_up and pinky_up:
            return GestureType.OK_SIGN

        # OPEN_PALM – all five fingers extended
        if all(fingers_up):
            return GestureType.OPEN_PALM

        # FIST – no fingers extended
        if extended_count == 0:
            return GestureType.FIST

        # THUMBS_UP – only thumb extended
        if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
            return GestureType.THUMBS_UP

        # POINTING_UP – only index finger extended
        if index_up and not thumb_up and not middle_up and not ring_up and not pinky_up:
            return GestureType.POINTING_UP

        # PEACE_SIGN / SCROLL_UP – index + middle up, others down
        if index_up and middle_up and not ring_up and not pinky_up:
            # Differentiate SCROLL_UP by wrist y-position relative to index tip
            wrist_y = landmarks[self._WRIST][1]
            index_tip_y = landmarks[self._INDEX_TIP][1]
            if wrist_y > index_tip_y + 0.15:
                return GestureType.SCROLL_UP
            return GestureType.PEACE_SIGN

        # SCROLL_DOWN – ring + pinky up, index + middle down
        if not index_up and not middle_up and ring_up and pinky_up:
            return GestureType.SCROLL_DOWN

        return GestureType.NONE

    def _is_finger_up(self, landmarks: list, finger_tip: int, finger_pip: int) -> bool:
        """Return True when the finger tip is above (lower y) its PIP joint."""
        # In normalised coords y increases downward; tip above pip → tip_y < pip_y
        return landmarks[finger_tip][1] < landmarks[finger_pip][1]

    def _calculate_distance(self, p1: tuple, p2: tuple) -> float:
        """Euclidean distance between two normalised (x, y) or (x, y, z) points."""
        return float(
            ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5
        )

    def _get_hand_center(self, landmarks: list) -> Tuple[float, float]:
        """Return the centroid (x, y) of all landmarks."""
        xs = [lm[0] for lm in landmarks]
        ys = [lm[1] for lm in landmarks]
        return (sum(xs) / len(xs), sum(ys) / len(ys))

    def _calculate_confidence(self, landmarks: list) -> float:
        """Estimate confidence from the spread of landmark positions.

        Larger hand spans generally correspond to more reliable detections.
        The value is clamped to [0.5, 1.0].
        """
        xs = [lm[0] for lm in landmarks]
        ys = [lm[1] for lm in landmarks]
        span = max(max(xs) - min(xs), max(ys) - min(ys))
        # Heuristic: span of ~0.4 (full frame) → confidence 1.0
        confidence = min(1.0, max(0.5, span / 0.4))
        return round(confidence, 3)

    def __del__(self) -> None:
        if self._hands is not None:
            try:
                self._hands.close()
            except Exception:
                pass
