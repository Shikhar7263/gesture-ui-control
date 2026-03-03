"""Tests for the Flask web application routes in app.py.

All tests use Flask's built-in test client and run without a real camera,
MediaPipe, pyautogui, or pynput — heavy dependencies are stubbed out
identically to test_gesture_detector.py.
"""

import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Stubs (must be installed before importing app)
# ---------------------------------------------------------------------------

def _install_stubs():
    # ── mediapipe ──────────────────────────────────────────────────────────
    mp = types.ModuleType("mediapipe")
    solutions = types.ModuleType("mediapipe.solutions")
    hands_mod = types.ModuleType("mediapipe.solutions.hands")
    drawing_mod = types.ModuleType("mediapipe.solutions.drawing_utils")
    styles_mod = types.ModuleType("mediapipe.solutions.drawing_styles")

    class FakeHands:
        HAND_CONNECTIONS = []
        def __init__(self, **kw): pass
        def process(self, img): return type("R", (), {"multi_hand_landmarks": None, "multi_handedness": None})()
        def close(self): pass

    hands_mod.Hands = FakeHands
    drawing_mod.draw_landmarks = lambda *a, **kw: None
    styles_mod.get_default_hand_landmarks_style = lambda: {}
    styles_mod.get_default_hand_connections_style = lambda: {}
    solutions.hands = hands_mod
    solutions.drawing_utils = drawing_mod
    solutions.drawing_styles = styles_mod
    mp.solutions = solutions
    for name, mod in [
        ("mediapipe", mp),
        ("mediapipe.solutions", solutions),
        ("mediapipe.solutions.hands", hands_mod),
        ("mediapipe.solutions.drawing_utils", drawing_mod),
        ("mediapipe.solutions.drawing_styles", styles_mod),
    ]:
        sys.modules.setdefault(name, mod)

    # ── cv2 ────────────────────────────────────────────────────────────────
    cv2 = types.ModuleType("cv2")
    cv2.COLOR_BGR2RGB = 4
    cv2.COLOR_RGB2BGR = 5
    cv2.cvtColor = lambda img, code: img
    cv2.putText = lambda *a, **kw: None
    cv2.FONT_HERSHEY_SIMPLEX = 0
    cv2.LINE_AA = 16
    cv2.imencode = lambda ext, frame: (True, MagicMock(tobytes=lambda: b"JPEG"))
    _fake_cap = MagicMock()
    _fake_cap.isOpened.return_value = False
    cv2.VideoCapture = MagicMock(return_value=_fake_cap)
    cv2.CAP_PROP_FRAME_WIDTH = 3
    cv2.CAP_PROP_FRAME_HEIGHT = 4
    sys.modules.setdefault("cv2", cv2)

    # ── pyautogui ──────────────────────────────────────────────────────────
    pag = types.ModuleType("pyautogui")
    pag.FAILSAFE = False
    pag.size = lambda: (1920, 1080)
    pag.moveTo = lambda *a, **kw: None
    pag.click = lambda *a, **kw: None
    pag.doubleClick = lambda *a, **kw: None
    pag.scroll = lambda *a, **kw: None
    sys.modules.setdefault("pyautogui", pag)

    # ── pynput ─────────────────────────────────────────────────────────────
    pynput = types.ModuleType("pynput")
    keyboard = types.ModuleType("pynput.keyboard")

    class FakeKey:
        page_up = "page_up"
        page_down = "page_down"
        enter = "enter"
        media_play_pause = "media_play_pause"
        media_stop = "media_stop"

    class FakeController:
        def press(self, key): pass
        def release(self, key): pass
        def type(self, text): pass

    keyboard.Key = FakeKey
    keyboard.Controller = FakeController
    pynput.keyboard = keyboard
    sys.modules.setdefault("pynput", pynput)
    sys.modules.setdefault("pynput.keyboard", keyboard)


_install_stubs()

# Now it is safe to import the Flask application.
from app import app as flask_app  # noqa: E402
from gesture_control.gesture_detector import GestureType  # noqa: E402

_GESTURE_COUNT = len(GestureType)
_HISTORY_MAXLEN = 20  # matches the deque(maxlen=20) in app.py


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Index route
# ---------------------------------------------------------------------------

class TestIndexRoute:
    def test_index_status_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_content_type_html(self, client):
        r = client.get("/")
        assert b"text/html" in r.content_type.encode()

    def test_index_contains_title(self, client):
        r = client.get("/")
        assert b"Gesture" in r.data


# ---------------------------------------------------------------------------
# /api/status
# ---------------------------------------------------------------------------

class TestApiStatus:
    def test_status_200(self, client):
        r = client.get("/api/status")
        assert r.status_code == 200

    def test_status_keys_present(self, client):
        data = client.get("/api/status").get_json()
        assert "is_running" in data
        assert "current_gesture" in data
        assert "camera_available" in data
        assert "history_count" in data

    def test_status_not_running_initially(self, client):
        data = client.get("/api/status").get_json()
        assert data["is_running"] is False

    def test_status_history_count_is_int(self, client):
        data = client.get("/api/status").get_json()
        assert isinstance(data["history_count"], int)


# ---------------------------------------------------------------------------
# /api/config  GET
# ---------------------------------------------------------------------------

class TestApiConfigGet:
    def test_config_get_200(self, client):
        r = client.get("/api/config")
        assert r.status_code == 200

    def test_config_get_returns_all_fields(self, client):
        data = client.get("/api/config").get_json()
        expected_keys = {
            "camera_index", "frame_width", "frame_height",
            "min_detection_confidence", "min_tracking_confidence",
            "mouse_smoothing", "click_cooldown", "gesture_cooldown",
            "scroll_speed", "enable_mouse_control", "enable_keyboard_control",
            "screen_margin",
        }
        assert expected_keys.issubset(data.keys())

    def test_config_default_camera_index(self, client):
        data = client.get("/api/config").get_json()
        assert data["camera_index"] == 0


# ---------------------------------------------------------------------------
# /api/config  POST
# ---------------------------------------------------------------------------

class TestApiConfigPost:
    def test_config_post_200(self, client):
        r = client.post("/api/config", json={"scroll_speed": 5})
        assert r.status_code == 200

    def test_config_post_returns_ok_status(self, client):
        data = client.post("/api/config", json={"scroll_speed": 5}).get_json()
        assert data["status"] == "ok"

    def test_config_post_updates_field(self, client):
        client.post("/api/config", json={"scroll_speed": 7})
        data = client.get("/api/config").get_json()
        assert data["scroll_speed"] == 7

    def test_config_post_ignores_unknown_keys(self, client):
        r = client.post("/api/config", json={"nonexistent_key": 999})
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "ok"

    def test_config_post_empty_body(self, client):
        r = client.post("/api/config", json={})
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# /api/gestures
# ---------------------------------------------------------------------------

class TestApiGestures:
    def test_gestures_200(self, client):
        r = client.get("/api/gestures")
        assert r.status_code == 200

    def test_gestures_returns_list(self, client):
        data = client.get("/api/gestures").get_json()
        assert isinstance(data, list)
        assert len(data) == _GESTURE_COUNT

    def test_gestures_each_has_name_value_description(self, client):
        data = client.get("/api/gestures").get_json()
        for entry in data:
            assert "name" in entry
            assert "value" in entry
            assert "description" in entry

    def test_gestures_includes_pinch(self, client):
        data = client.get("/api/gestures").get_json()
        values = [g["value"] for g in data]
        assert "pinch" in values

    def test_gestures_includes_none(self, client):
        data = client.get("/api/gestures").get_json()
        values = [g["value"] for g in data]
        assert "none" in values


# ---------------------------------------------------------------------------
# /api/history
# ---------------------------------------------------------------------------

class TestApiHistory:
    def test_history_200(self, client):
        r = client.get("/api/history")
        assert r.status_code == 200

    def test_history_returns_list(self, client):
        data = client.get("/api/history").get_json()
        assert isinstance(data, list)

    def test_history_at_most_20_entries(self, client):
        data = client.get("/api/history").get_json()
        assert len(data) <= _HISTORY_MAXLEN


# ---------------------------------------------------------------------------
# /api/start  and  /api/stop
# ---------------------------------------------------------------------------

class TestApiStartStop:
    def test_stop_when_not_running(self, client):
        r = client.post("/api/stop")
        assert r.status_code == 200
        data = r.get_json()
        assert data["status"] == "stopped"

    def test_stop_sets_not_running(self, client):
        client.post("/api/stop")
        status = client.get("/api/status").get_json()
        assert status["is_running"] is False

    def test_start_returns_json(self, client):
        r = client.post("/api/start")
        assert r.status_code == 200
        data = r.get_json()
        assert "status" in data

    def test_double_start_returns_already_running_or_started(self, client):
        # First start may succeed or fail depending on camera; second call
        # when already running must return already_running.
        client.post("/api/start")
        r2 = client.post("/api/start")
        data = r2.get_json()
        assert data["status"] in ("started", "already_running")
        # Ensure the app is stopped cleanly for subsequent tests
        client.post("/api/stop")
