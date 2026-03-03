"""Tests for the Flask web application routes.

All tests use the Flask test client and run without a physical camera,
MediaPipe, pyautogui, or pynput.  External dependencies are stubbed at the
module level before importing the app under test.
"""

import sys
import types
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Reuse the same lightweight stubs as test_gesture_detector.py
# ---------------------------------------------------------------------------

def _ensure_stub(name, module):
    sys.modules.setdefault(name, module)


def _make_mediapipe_stub():
    mp = types.ModuleType("mediapipe")
    solutions = types.ModuleType("mediapipe.solutions")
    hands_mod = types.ModuleType("mediapipe.solutions.hands")
    drawing_mod = types.ModuleType("mediapipe.solutions.drawing_utils")
    styles_mod = types.ModuleType("mediapipe.solutions.drawing_styles")

    class FakeHands:
        HAND_CONNECTIONS = []
        def __init__(self, **kw): pass
        def process(self, img):
            result = MagicMock()
            result.multi_hand_landmarks = None
            result.multi_handedness = None
            return result
        def close(self): pass

    hands_mod.Hands = FakeHands
    drawing_mod.draw_landmarks = lambda *a, **kw: None
    styles_mod.get_default_hand_landmarks_style = lambda: {}
    styles_mod.get_default_hand_connections_style = lambda: {}
    solutions.hands = hands_mod
    solutions.drawing_utils = drawing_mod
    solutions.drawing_styles = styles_mod
    mp.solutions = solutions
    return mp, solutions, hands_mod, drawing_mod, styles_mod


def _make_cv2_stub():
    cv2 = types.ModuleType("cv2")
    cv2.COLOR_BGR2RGB = 4
    cv2.COLOR_RGB2BGR = 5
    cv2.cvtColor = lambda img, code: img
    cv2.putText = lambda *a, **kw: None
    cv2.FONT_HERSHEY_SIMPLEX = 0
    cv2.LINE_AA = 16
    cv2.imencode = lambda ext, frame: (True, MagicMock(tobytes=lambda: b""))
    cv2.CAP_PROP_FRAME_WIDTH = 3
    cv2.CAP_PROP_FRAME_HEIGHT = 4

    class FakeVideoCapture:
        """Stub VideoCapture that reports the camera as unavailable."""
        def __init__(self, *args, **kwargs): pass
        def isOpened(self): return False
        def set(self, prop, value): pass
        def read(self): return False, None
        def release(self): pass

    cv2.VideoCapture = FakeVideoCapture
    return cv2


def _make_pyautogui_stub():
    pag = types.ModuleType("pyautogui")
    pag.FAILSAFE = False
    pag.size = lambda: (1920, 1080)
    pag.moveTo = lambda *a, **kw: None
    pag.click = lambda *a, **kw: None
    pag.doubleClick = lambda *a, **kw: None
    pag.scroll = lambda *a, **kw: None
    return pag


def _make_pynput_stub():
    pynput = types.ModuleType("pynput")
    keyboard = types.ModuleType("pynput.keyboard")

    class FakeKey:
        page_up = "page_up"
        page_down = "page_down"
        media_play_pause = "media_play_pause"
        media_stop = "media_stop"

    class FakeController:
        def press(self, key): pass
        def release(self, key): pass
        def type(self, text): pass

    keyboard.Key = FakeKey
    keyboard.Controller = FakeController
    pynput.keyboard = keyboard
    return pynput, keyboard


# Install stubs (idempotent — setdefault won't overwrite if already present)
_mp, *_mp_sub = _make_mediapipe_stub()
_ensure_stub("mediapipe", _mp)
_ensure_stub("mediapipe.solutions", _mp_sub[0])
_ensure_stub("mediapipe.solutions.hands", _mp_sub[1])
_ensure_stub("mediapipe.solutions.drawing_utils", _mp_sub[2])
_ensure_stub("mediapipe.solutions.drawing_styles", _mp_sub[3])

_cv2 = _make_cv2_stub()
_ensure_stub("cv2", _cv2)

_pag = _make_pyautogui_stub()
_ensure_stub("pyautogui", _pag)

_pynput, _pynput_kb = _make_pynput_stub()
_ensure_stub("pynput", _pynput)
_ensure_stub("pynput.keyboard", _pynput_kb)

# Now it is safe to import the Flask app
from gesture_control.config import Config  # noqa: E402 – stubs must be installed first
import app as flask_app  # noqa: E402 – stubs must be installed first


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """Return a Flask test client with testing mode enabled."""
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        # Reset global state before each test
        flask_app.is_running = False
        flask_app.current_gesture = "none"
        flask_app.gesture_history.clear()
        flask_app.config = Config()
        yield c


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndexRoute:
    def test_index_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_index_returns_html(self, client):
        resp = client.get("/")
        assert b"Gesture" in resp.data


# ---------------------------------------------------------------------------
# GET /api/status
# ---------------------------------------------------------------------------

class TestApiStatus:
    def test_status_keys(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "is_running" in data
        assert "current_gesture" in data
        assert "camera_available" in data
        assert "history_count" in data

    def test_status_not_running_by_default(self, client):
        resp = client.get("/api/status")
        data = resp.get_json()
        assert data["is_running"] is False

    def test_status_history_count_zero(self, client):
        resp = client.get("/api/status")
        data = resp.get_json()
        assert data["history_count"] == 0


# ---------------------------------------------------------------------------
# GET /api/config
# ---------------------------------------------------------------------------

class TestApiConfigGet:
    def test_config_returns_200(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200

    def test_config_contains_expected_keys(self, client):
        resp = client.get("/api/config")
        data = resp.get_json()
        assert "camera_index" in data
        assert "frame_width" in data
        assert "frame_height" in data
        assert "mouse_smoothing" in data
        assert "scroll_speed" in data
        assert "enable_mouse_control" in data
        assert "enable_keyboard_control" in data

    def test_config_default_scroll_speed(self, client):
        resp = client.get("/api/config")
        data = resp.get_json()
        assert data["scroll_speed"] == 3


# ---------------------------------------------------------------------------
# POST /api/config
# ---------------------------------------------------------------------------

class TestApiConfigPost:
    def test_save_valid_key(self, client):
        resp = client.post(
            "/api/config",
            json={"scroll_speed": 7},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["config"]["scroll_speed"] == 7

    def test_unknown_key_ignored(self, client):
        resp = client.post(
            "/api/config",
            json={"nonexistent_key": 999},
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_empty_body_accepted(self, client):
        resp = client.post(
            "/api/config",
            json={},
            content_type="application/json",
        )
        assert resp.status_code == 200

    def test_toggle_mouse_control_off(self, client):
        resp = client.post(
            "/api/config",
            json={"enable_mouse_control": False},
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["config"]["enable_mouse_control"] is False


# ---------------------------------------------------------------------------
# GET /api/gestures
# ---------------------------------------------------------------------------

class TestApiGestures:
    def test_gestures_returns_list(self, client):
        resp = client.get("/api/gestures")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_gestures_count(self, client):
        resp = client.get("/api/gestures")
        data = resp.get_json()
        # Count must match the number of GestureType enum members
        from gesture_control.gesture_detector import GestureType
        assert len(data) == len(GestureType)

    def test_gestures_have_required_fields(self, client):
        resp = client.get("/api/gestures")
        data = resp.get_json()
        for entry in data:
            assert "name" in entry
            assert "value" in entry
            assert "description" in entry

    def test_none_gesture_present(self, client):
        resp = client.get("/api/gestures")
        data = resp.get_json()
        values = [g["value"] for g in data]
        assert "none" in values

    def test_pinch_gesture_present(self, client):
        resp = client.get("/api/gestures")
        data = resp.get_json()
        values = [g["value"] for g in data]
        assert "pinch" in values


# ---------------------------------------------------------------------------
# GET /api/history
# ---------------------------------------------------------------------------

class TestApiHistory:
    def test_history_empty_by_default(self, client):
        resp = client.get("/api/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data == []

    def test_history_returns_list(self, client):
        resp = client.get("/api/history")
        data = resp.get_json()
        assert isinstance(data, list)

    def test_history_reflects_added_entries(self, client):
        flask_app.gesture_history.append({
            "gesture": "pinch",
            "confidence": 0.9,
            "timestamp": "12:00:00",
        })
        resp = client.get("/api/history")
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["gesture"] == "pinch"


# ---------------------------------------------------------------------------
# POST /api/start
# ---------------------------------------------------------------------------

class TestApiStart:
    def test_start_returns_200(self, client):
        resp = client.post("/api/start")
        assert resp.status_code == 200

    def test_start_response_has_status(self, client):
        resp = client.post("/api/start")
        data = resp.get_json()
        assert "status" in data

    def test_double_start_returns_already_running(self, client):
        flask_app.is_running = True
        resp = client.post("/api/start")
        data = resp.get_json()
        assert data["status"] == "already_running"


# ---------------------------------------------------------------------------
# POST /api/stop
# ---------------------------------------------------------------------------

class TestApiStop:
    def test_stop_returns_200(self, client):
        resp = client.post("/api/stop")
        assert resp.status_code == 200

    def test_stop_response_has_status(self, client):
        resp = client.post("/api/stop")
        data = resp.get_json()
        assert data["status"] == "stopped"

    def test_stop_sets_not_running(self, client):
        flask_app.is_running = True
        client.post("/api/stop")
        assert flask_app.is_running is False
