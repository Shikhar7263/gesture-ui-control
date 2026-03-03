"""Stage 2 — System Control (Mouse + Keyboard).

Extends Stage 1 by wiring detected gestures to real mouse and keyboard
actions on the host OS.  No web server.

Usage::

    python stages/stage2_system_control.py

Press **q** in the preview window (or Ctrl+C in the terminal) to quit.

Mouse / keyboard actions can be toggled by editing config.json:

    "enable_mouse_control": true,
    "enable_keyboard_control": true
"""

import sys
import os
import time

# Allow running from the repo root or from the stages/ subdirectory.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2

from gesture_control.config import load_config
from gesture_control.gesture_detector import GestureDetector, GestureType
from gesture_control.mouse_controller import MouseController
from gesture_control.keyboard_controller import KeyboardController


def main() -> None:
    config = load_config()

    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        print(f"[Stage 2] Could not open camera index {config.camera_index}.")
        print("          Check 'camera_index' in config.json and try again.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)

    detector = GestureDetector(config)
    mouse = MouseController(config)
    keyboard = KeyboardController(config)

    last_gesture = GestureType.NONE

    print("[Stage 2] System Control running — press q to quit.")
    print(f"          Mouse control  : {'ON' if config.enable_mouse_control else 'OFF'}")
    print(f"          Keyboard control: {'ON' if config.enable_keyboard_control else 'OFF'}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            annotated, result = detector.process_frame(frame)

            # Console output on gesture change.
            if result.gesture != last_gesture:
                last_gesture = result.gesture
                label = result.gesture.value.replace("_", " ").upper()
                conf = int(result.confidence * 100)
                print(f"  Gesture: {label:<20}  Confidence: {conf}%")

            # System control actions.
            if result.gesture != GestureType.NONE:
                if config.enable_mouse_control and result.landmarks:
                    mouse.move_cursor(
                        result.hand_center,
                        (config.frame_width, config.frame_height),
                    )

                if result.gesture == GestureType.PINCH:
                    mouse.left_click()
                elif result.gesture == GestureType.SCROLL_UP:
                    mouse.scroll("up")
                elif result.gesture == GestureType.SCROLL_DOWN:
                    mouse.scroll("down")

                if config.enable_keyboard_control:
                    keyboard.handle_gesture_key(result.gesture)

            cv2.imshow("Stage 2 — System Control", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.033)  # ~30 fps
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[Stage 2] Stopped.")


if __name__ == "__main__":
    main()
