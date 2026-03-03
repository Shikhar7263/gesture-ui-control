"""Tests for the Gesture Control system.

All tests are designed to run without a physical camera, MediaPipe, or any
display environment.  External dependencies (mediapipe, cv2, pyautogui,
pynput) are mocked at the module level before the system under test is
imported.
"""

import importlib
import sys
import types
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Lightweight stubs for optional heavy dependencies
# ---------------------------------------------------------------------------

def _make_mediapipe_stub():
    """Return a minimal mediapipe stub that satisfies import-time references."""
    mp = types.ModuleType("mediapipe")
    solutions = types.ModuleType("mediapipe.solutions")
    hands_mod = types.ModuleType("mediapipe.solutions.hands")
    drawing_mod = types.ModuleType("mediapipe.solutions.drawing_utils")
    styles_mod = types.ModuleType("mediapipe.solutions.drawing_styles")

    # Hands class stub
    class FakeHands:
        HAND_CONNECTIONS = []
        def __init__(self, **kw): pass
        def process(self, img): return FakeResult()
        def close(self): pass

    class FakeResult:
        multi_hand_landmarks = None
        multi_handedness = None

    hands_mod.Hands = FakeHands

    drawing_mod.draw_landmarks = lambda *a, **kw: None

    def fake_style(): return {}
    styles_mod.get_default_hand_landmarks_style = fake_style
    styles_mod.get_default_hand_connections_style = fake_style

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
    cv2.VideoCapture = MagicMock
    cv2.CAP_PROP_FRAME_WIDTH = 3
    cv2.CAP_PROP_FRAME_HEIGHT = 4
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
    return pynput, keyboard


# Install stubs before importing any project module
_mp, *_mp_sub = _make_mediapipe_stub()
sys.modules.setdefault("mediapipe", _mp)
sys.modules.setdefault("mediapipe.solutions", _mp_sub[0])
sys.modules.setdefault("mediapipe.solutions.hands", _mp_sub[1])
sys.modules.setdefault("mediapipe.solutions.drawing_utils", _mp_sub[2])
sys.modules.setdefault("mediapipe.solutions.drawing_styles", _mp_sub[3])

_cv2 = _make_cv2_stub()
sys.modules.setdefault("cv2", _cv2)

_pag = _make_pyautogui_stub()
sys.modules.setdefault("pyautogui", _pag)

_pynput, _pynput_kb = _make_pynput_stub()
sys.modules.setdefault("pynput", _pynput)
sys.modules.setdefault("pynput.keyboard", _pynput_kb)

import numpy as np  # numpy is a real dependency used in app; install it

# Now import project modules
from gesture_control.config import Config, load_config, save_config
from gesture_control.gesture_detector import GestureDetector, GestureResult, GestureType
from gesture_control.keyboard_controller import KeyboardController
from gesture_control.mouse_controller import MouseController


# ---------------------------------------------------------------------------
# GestureType enum tests
# ---------------------------------------------------------------------------

class TestGestureTypeEnum:
    def test_none_value(self):
        assert GestureType.NONE.value == "none"

    def test_pinch_value(self):
        assert GestureType.PINCH.value == "pinch"

    def test_thumbs_up_value(self):
        assert GestureType.THUMBS_UP.value == "thumbs_up"

    def test_peace_sign_value(self):
        assert GestureType.PEACE_SIGN.value == "peace_sign"

    def test_fist_value(self):
        assert GestureType.FIST.value == "fist"

    def test_open_palm_value(self):
        assert GestureType.OPEN_PALM.value == "open_palm"

    def test_ok_sign_value(self):
        assert GestureType.OK_SIGN.value == "ok_sign"

    def test_pointing_up_value(self):
        assert GestureType.POINTING_UP.value == "pointing_up"

    def test_scroll_up_value(self):
        assert GestureType.SCROLL_UP.value == "scroll_up"

    def test_scroll_down_value(self):
        assert GestureType.SCROLL_DOWN.value == "scroll_down"

    def test_total_count(self):
        assert len(GestureType) == 10


# ---------------------------------------------------------------------------
# GestureResult dataclass tests
# ---------------------------------------------------------------------------

class TestGestureResult:
    def test_defaults(self):
        r = GestureResult()
        assert r.gesture == GestureType.NONE
        assert r.confidence == 0.0
        assert r.landmarks == []
        assert r.hand_center == (0.0, 0.0)

    def test_custom_values(self):
        lm = [(0.1, 0.2, 0.0)]
        r = GestureResult(
            gesture=GestureType.PINCH,
            confidence=0.95,
            landmarks=lm,
            hand_center=(0.5, 0.5),
        )
        assert r.gesture == GestureType.PINCH
        assert r.confidence == 0.95
        assert r.landmarks is lm
        assert r.hand_center == (0.5, 0.5)


# ---------------------------------------------------------------------------
# Config dataclass tests
# ---------------------------------------------------------------------------

class TestConfig:
    def test_default_values(self):
        c = Config()
        assert c.camera_index == 0
        assert c.frame_width == 640
        assert c.frame_height == 480
        assert c.min_detection_confidence == 0.7
        assert c.min_tracking_confidence == 0.7
        assert c.mouse_smoothing == 0.5
        assert c.click_cooldown == 0.3
        assert c.gesture_cooldown == 0.5
        assert c.scroll_speed == 3
        assert c.enable_mouse_control is True
        assert c.enable_keyboard_control is True
        assert c.screen_margin == 50

    def test_override_fields(self):
        c = Config(camera_index=1, scroll_speed=10)
        assert c.camera_index == 1
        assert c.scroll_speed == 10


# ---------------------------------------------------------------------------
# load_config / save_config tests
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_returns_config_instance(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        cfg = load_config()
        assert isinstance(cfg, Config)

    def test_loads_from_json(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import json
        (tmp_path / "config.json").write_text(json.dumps({"scroll_speed": 7}))
        cfg = load_config()
        assert cfg.scroll_speed == 7

    def test_ignores_unknown_keys(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import json
        (tmp_path / "config.json").write_text(json.dumps({"unknown_key": 99}))
        cfg = load_config()
        assert isinstance(cfg, Config)

    def test_invalid_json_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "config.json").write_text("NOT JSON {{{")
        cfg = load_config()
        assert cfg == Config()

    def test_save_and_reload(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        original = Config(scroll_speed=15, screen_margin=80)
        save_config(original)
        reloaded = load_config()
        assert reloaded.scroll_speed == 15
        assert reloaded.screen_margin == 80


# ---------------------------------------------------------------------------
# MouseController tests
# ---------------------------------------------------------------------------

class TestMouseController:
    def test_init(self):
        mc = MouseController(Config())
        assert mc is not None

    def test_get_screen_size(self):
        mc = MouseController(Config())
        w, h = mc.get_screen_size()
        assert w > 0 and h > 0

    def test_move_cursor_does_not_raise(self):
        mc = MouseController(Config())
        mc.move_cursor((0.5, 0.5), (640, 480))

    def test_left_click_disabled(self):
        cfg = Config(enable_mouse_control=False)
        mc = MouseController(cfg)
        result = mc.left_click()
        assert result is False

    def test_right_click_disabled(self):
        cfg = Config(enable_mouse_control=False)
        mc = MouseController(cfg)
        result = mc.right_click()
        assert result is False

    def test_scroll_does_not_raise(self):
        mc = MouseController(Config())
        mc.scroll("up")
        mc.scroll("down", amount=5)


# ---------------------------------------------------------------------------
# KeyboardController tests
# ---------------------------------------------------------------------------

class TestKeyboardController:
    def test_init(self):
        kc = KeyboardController(Config())
        assert kc is not None

    def test_press_key_disabled(self):
        cfg = Config(enable_keyboard_control=False)
        kc = KeyboardController(cfg)
        result = kc.press_key("a")
        assert result is False

    def test_type_text_disabled(self):
        cfg = Config(enable_keyboard_control=False)
        kc = KeyboardController(cfg)
        kc.type_text("hello")  # should not raise

    def test_handle_gesture_key_scroll_up(self):
        kc = KeyboardController(Config())
        # Should map SCROLL_UP → page_up and succeed (stub controller)
        result = kc.handle_gesture_key(GestureType.SCROLL_UP)
        assert result is True

    def test_handle_gesture_key_no_mapping(self):
        kc = KeyboardController(Config())
        result = kc.handle_gesture_key(GestureType.NONE)
        assert result is False

    def test_hotkey_does_not_raise(self):
        kc = KeyboardController(Config())
        kc.hotkey("ctrl", "c")


# ---------------------------------------------------------------------------
# GestureDetector tests (isolated – no real MediaPipe)
# ---------------------------------------------------------------------------

def _fake_landmark_list(positions: dict, total: int = 21):
    """Build a list of (x, y, z) tuples mimicking MediaPipe normalised coords.

    positions is a mapping of landmark_index -> (x, y, z).
    Unspecified indices default to (0.5, 0.5, 0.0).
    """
    return [positions.get(i, (0.5, 0.5, 0.0)) for i in range(total)]


class TestGestureDetectorIsolated:
    """Tests for private gesture-detection helpers using synthetic landmarks."""

    def setup_method(self):
        self.detector = GestureDetector(Config())

    # _is_finger_up
    def test_finger_up_when_tip_above_pip(self):
        lm = _fake_landmark_list({8: (0.5, 0.2, 0.0), 6: (0.5, 0.5, 0.0)})
        assert self.detector._is_finger_up(lm, 8, 6) is True

    def test_finger_down_when_tip_below_pip(self):
        lm = _fake_landmark_list({8: (0.5, 0.8, 0.0), 6: (0.5, 0.5, 0.0)})
        assert self.detector._is_finger_up(lm, 8, 6) is False

    # _calculate_distance
    def test_distance_zero_same_point(self):
        p = (0.3, 0.4, 0.0)
        assert self.detector._calculate_distance(p, p) == pytest.approx(0.0)

    def test_distance_known_value(self):
        p1 = (0.0, 0.0, 0.0)
        p2 = (0.3, 0.4, 0.0)
        assert self.detector._calculate_distance(p1, p2) == pytest.approx(0.5)

    # _get_hand_center
    def test_hand_center_uniform(self):
        lm = [(0.4, 0.6, 0.0)] * 21
        cx, cy = self.detector._get_hand_center(lm)
        assert cx == pytest.approx(0.4)
        assert cy == pytest.approx(0.6)

    # _calculate_confidence
    def test_confidence_in_range(self):
        lm = _fake_landmark_list({})
        conf = self.detector._calculate_confidence(lm)
        assert 0.0 <= conf <= 1.0

    # _detect_gesture – OPEN_PALM
    def test_detect_open_palm(self):
        # All finger tips above their PIP joints.
        # Thumb tip (4) and index tip (8) are >0.10 apart to avoid OK_SIGN.
        lm = _fake_landmark_list({
            # Thumb: tip(4) far left, well above ip(3)
            4: (0.05, 0.1, 0), 3: (0.05, 0.35, 0),
            # Index: tip(8) above pip(6)
            8: (0.35, 0.1, 0), 6: (0.35, 0.4, 0),
            # Middle: tip(12) above pip(10)
            12: (0.50, 0.1, 0), 10: (0.50, 0.4, 0),
            # Ring: tip(16) above pip(14)
            16: (0.65, 0.1, 0), 14: (0.65, 0.4, 0),
            # Pinky: tip(20) above pip(18)
            20: (0.80, 0.1, 0), 18: (0.80, 0.4, 0),
        })
        gesture = self.detector._detect_gesture(lm, "Right")
        assert gesture == GestureType.OPEN_PALM

    # _detect_gesture – FIST (all fingers down)
    def test_detect_fist(self):
        lm = _fake_landmark_list({
            4: (0.2, 0.9, 0), 3: (0.2, 0.3, 0),   # thumb down
            8: (0.3, 0.9, 0), 6: (0.3, 0.4, 0),   # index down
            12: (0.4, 0.9, 0), 10: (0.4, 0.4, 0), # middle down
            16: (0.5, 0.9, 0), 14: (0.5, 0.4, 0), # ring down
            20: (0.6, 0.9, 0), 18: (0.6, 0.4, 0), # pinky down
        })
        gesture = self.detector._detect_gesture(lm, "Right")
        assert gesture == GestureType.FIST

    # _detect_gesture – PINCH (thumb tip very close to index tip)
    def test_detect_pinch(self):
        lm = _fake_landmark_list({
            4: (0.5, 0.5, 0),    # thumb tip
            8: (0.502, 0.5, 0),  # index tip – distance < 0.05
        })
        gesture = self.detector._detect_gesture(lm, "Right")
        assert gesture == GestureType.PINCH

    # _detect_gesture – POINTING_UP
    def test_detect_pointing_up(self):
        lm = _fake_landmark_list({
            4: (0.2, 0.8, 0), 3: (0.2, 0.3, 0),   # thumb down
            8: (0.3, 0.1, 0), 6: (0.3, 0.4, 0),   # index UP
            12: (0.4, 0.9, 0), 10: (0.4, 0.4, 0), # middle down
            16: (0.5, 0.9, 0), 14: (0.5, 0.4, 0), # ring down
            20: (0.6, 0.9, 0), 18: (0.6, 0.4, 0), # pinky down
        })
        gesture = self.detector._detect_gesture(lm, "Right")
        assert gesture == GestureType.POINTING_UP

    # process_frame with stub cv2 (no real camera)
    def test_process_frame_returns_tuple(self):
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype="uint8")
        annotated, result = self.detector.process_frame(frame)
        assert isinstance(result, GestureResult)
