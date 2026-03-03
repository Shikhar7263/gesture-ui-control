"""Stage 1 — Gesture Detection Core.

Runs hand-gesture detection using MediaPipe and OpenCV and prints each
detected gesture to the console.  No mouse control, no keyboard control,
no web server.

Usage::

    python stages/stage1_gesture_detection.py

Press **q** in the preview window (or Ctrl+C in the terminal) to quit.
"""

import sys
import os
import time

# Allow running from the repo root or from the stages/ subdirectory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2

from gesture_control.config import load_config
from gesture_control.gesture_detector import GestureDetector, GestureType


def main() -> None:
    config = load_config()

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        print(f"[Stage 1] Could not open camera index {config.camera_index}.")
        print("          Check 'camera_index' in config.json and try again.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    detector = GestureDetector(config)
    last_gesture = GestureType.NONE

    print("[Stage 1] Gesture Detection running — press q to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            annotated, result = detector.process_frame(frame)

            # Print to console only when the gesture changes.
            if result.gesture != last_gesture:
                last_gesture = result.gesture
                label = result.gesture.value.replace("_", " ").upper()
                conf = int(result.confidence * 100)
                print(f"  Gesture: {label:<20}  Confidence: {conf}%")

            cv2.imshow("Stage 1 — Gesture Detection", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.033)  # ~30 fps
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[Stage 1] Stopped.")


if __name__ == "__main__":
    main()
