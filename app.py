"""Flask web application for the Gesture-Based UI Control System."""

import base64
import json
import os
import threading
import time
from collections import deque
from dataclasses import asdict
from typing import Optional

import cv2
from flask import Flask, Response, jsonify, render_template, request
from flask_socketio import SocketIO, emit

from gesture_control.config import Config, load_config, save_config
from gesture_control.gesture_detector import GestureDetector, GestureType
from gesture_control.keyboard_controller import KeyboardController
from gesture_control.mouse_controller import MouseController

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gesture-ui-dev-secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
config: Config = load_config()
gesture_detector: Optional[GestureDetector] = None
mouse_controller: Optional[MouseController] = None
keyboard_controller: Optional[KeyboardController] = None
camera: Optional[cv2.VideoCapture] = None
is_running: bool = False
current_gesture: str = GestureType.NONE.value
gesture_history: deque = deque(maxlen=20)

_camera_lock = threading.Lock()
_bg_thread: Optional[threading.Thread] = None

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _make_placeholder_frame(message: str = "Camera not available"):
    """Create a black placeholder frame with a text message."""
    import numpy as np
    frame = np.zeros((480, 640, 3), dtype="uint8")
    cv2.putText(
        frame, message, (80, 240),
        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA,
    )
    return frame


def _open_camera() -> Optional[cv2.VideoCapture]:
    """Try to open the configured camera; return None on failure."""
    cap = cv2.VideoCapture(config.camera_index)
    if not cap.isOpened():
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.frame_height)
    return cap


def _init_components() -> None:
    """Instantiate detector and controller objects from current config."""
    global gesture_detector, mouse_controller, keyboard_controller
    gesture_detector = GestureDetector(config)
    mouse_controller = MouseController(config)
    keyboard_controller = KeyboardController(config)


# ---------------------------------------------------------------------------
# Background processing thread
# ---------------------------------------------------------------------------

def _process_frames() -> None:
    """Read frames from the camera, detect gestures, emit SocketIO events."""
    global current_gesture, camera

    while is_running:
        with _camera_lock:
            cap = camera
            if cap is None or not cap.isOpened():
                time.sleep(0.1)
                continue
            ret, frame = cap.read()

        if not ret:
            time.sleep(0.05)
            continue

        annotated, result = gesture_detector.process_frame(frame)
        gesture_label = result.gesture.value

        if gesture_label != current_gesture:
            current_gesture = gesture_label
            entry = {
                "gesture": gesture_label,
                "confidence": round(result.confidence, 3),
                "timestamp": time.strftime("%H:%M:%S"),
            }
            gesture_history.append(entry)
            socketio.emit("gesture_event", entry)

        # Mouse / keyboard handling
        if result.gesture not in (GestureType.NONE,):
            if config.enable_mouse_control and result.landmarks:
                mouse_controller.move_cursor(result.hand_center, (config.frame_width, config.frame_height))

            if result.gesture == GestureType.PINCH:
                mouse_controller.left_click()
            elif result.gesture == GestureType.SCROLL_UP:
                mouse_controller.scroll("up")
            elif result.gesture == GestureType.SCROLL_DOWN:
                mouse_controller.scroll("down")

            if config.enable_keyboard_control:
                keyboard_controller.handle_gesture_key(result.gesture)

        time.sleep(0.033)  # ~30 fps


# ---------------------------------------------------------------------------
# MJPEG frame generator
# ---------------------------------------------------------------------------

def generate_frames():
    """Yield JPEG frames for the MJPEG video feed endpoint."""
    while True:
        frame = None
        with _camera_lock:
            cap = camera
            if cap is not None and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    frame = None

        if frame is None:
            frame = _make_placeholder_frame()

        if is_running and gesture_detector is not None:
            try:
                frame, _ = gesture_detector.process_frame(frame)
            except Exception:
                pass

        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
        time.sleep(0.033)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    return jsonify({
        "is_running": is_running,
        "current_gesture": current_gesture,
        "camera_available": camera is not None and camera.isOpened(),
        "history_count": len(gesture_history),
    })


@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify(asdict(config))


@app.route("/api/config", methods=["POST"])
def api_config_post():
    global config
    data = request.get_json(silent=True) or {}
    valid_keys = Config.__dataclass_fields__.keys()
    current = asdict(config)
    current.update({k: v for k, v in data.items() if k in valid_keys})
    config = Config(**current)
    save_config(config)
    if gesture_detector:
        _init_components()
    return jsonify({"status": "ok", "config": asdict(config)})


@app.route("/api/gestures")
def api_gestures():
    gestures = [
        {"name": g.name, "value": g.value, "description": _gesture_description(g)}
        for g in GestureType
    ]
    return jsonify(gestures)


@app.route("/api/history")
def api_history():
    return jsonify(list(gesture_history)[-20:])


@app.route("/api/start", methods=["POST"])
def api_start():
    global is_running, camera, _bg_thread
    if is_running:
        return jsonify({"status": "already_running"})

    _init_components()
    with _camera_lock:
        camera = _open_camera()

    is_running = True
    _bg_thread = threading.Thread(target=_process_frames, daemon=True)
    _bg_thread.start()
    return jsonify({"status": "started"})


@app.route("/api/stop", methods=["POST"])
def api_stop():
    global is_running, camera
    is_running = False
    with _camera_lock:
        if camera is not None:
            camera.release()
            camera = None
    return jsonify({"status": "stopped"})


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


# ---------------------------------------------------------------------------
# SocketIO events
# ---------------------------------------------------------------------------

@socketio.on("connect")
def on_connect():
    emit("status", {"is_running": is_running, "current_gesture": current_gesture})


@socketio.on("disconnect")
def on_disconnect():
    pass


# ---------------------------------------------------------------------------
# Gesture descriptions
# ---------------------------------------------------------------------------

def _gesture_description(g: GestureType) -> str:
    descriptions = {
        GestureType.NONE: "No gesture detected",
        GestureType.PINCH: "Thumb + index tip together — left click",
        GestureType.THUMBS_UP: "Thumb extended upward — play/pause media",
        GestureType.PEACE_SIGN: "Index + middle fingers up — peace sign",
        GestureType.FIST: "All fingers curled — stop media",
        GestureType.OPEN_PALM: "All 5 fingers extended — open palm",
        GestureType.OK_SIGN: "Thumb + index circle — OK",
        GestureType.POINTING_UP: "Only index finger extended — pointing up",
        GestureType.SCROLL_UP: "Index + middle pointing high — scroll up",
        GestureType.SCROLL_DOWN: "Ring + pinky up — scroll down",
    }
    return descriptions.get(g, "")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    host = os.environ.get("GESTURE_HOST", "127.0.0.1")
    port = int(os.environ.get("GESTURE_PORT", "5000"))
    socketio.run(app, host=host, port=port, debug=False)
