"""Keyboard simulation using pynput with cooldown support."""

import time

try:
    from pynput import keyboard as pynput_keyboard
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False

from gesture_control.config import Config
from gesture_control.gesture_detector import GestureType


# Mapping from gesture type to keyboard action description
_GESTURE_KEY_MAP = {
    GestureType.SCROLL_UP: "page_up",
    GestureType.SCROLL_DOWN: "page_down",
    GestureType.THUMBS_UP: "media_play_pause",
    GestureType.FIST: "media_stop",
}


class KeyboardController:
    """Simulates keyboard input in response to gesture events."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._last_key_time: float = 0.0
        self._controller = None

        if _PYNPUT_AVAILABLE:
            self._controller = pynput_keyboard.Controller()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def press_key(self, key: str) -> bool:
        """Press and release *key* if the gesture cooldown has elapsed.

        Args:
            key: A character string (e.g. ``"a"``) or a pynput Key name
                 (e.g. ``"page_up"``, ``"enter"``).

        Returns:
            ``True`` if the key was sent successfully.
        """
        if not _PYNPUT_AVAILABLE or not self._config.enable_keyboard_control:
            return False
        if time.time() - self._last_key_time < self._config.gesture_cooldown:
            return False

        pynput_key = self._resolve_key(key)
        if pynput_key is None:
            return False

        try:
            self._controller.press(pynput_key)
            self._controller.release(pynput_key)
            self._last_key_time = time.time()
            return True
        except Exception:
            return False

    def type_text(self, text: str) -> None:
        """Type a string of characters."""
        if not _PYNPUT_AVAILABLE or not self._config.enable_keyboard_control:
            return
        try:
            self._controller.type(text)
        except Exception:
            pass

    def hotkey(self, *keys: str) -> None:
        """Press a key combination (all keys held simultaneously).

        Example::

            hotkey("ctrl", "c")  # Copy
        """
        if not _PYNPUT_AVAILABLE or not self._config.enable_keyboard_control:
            return

        resolved = [self._resolve_key(k) for k in keys]
        resolved = [k for k in resolved if k is not None]
        if not resolved:
            return

        try:
            for k in resolved:
                self._controller.press(k)
            for k in reversed(resolved):
                self._controller.release(k)
        except Exception:
            pass

    def handle_gesture_key(self, gesture_type: GestureType) -> bool:
        """Translate *gesture_type* to a keyboard action if one is mapped.

        Returns ``True`` when a key was triggered.
        """
        key_name = _GESTURE_KEY_MAP.get(gesture_type)
        if key_name is None:
            return False
        return self.press_key(key_name)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_key(self, key: str):
        """Return a pynput Key or character for *key*.

        Tries ``pynput_keyboard.Key.<key>`` first; falls back to the raw
        character so that single-char strings work directly.
        """
        if not _PYNPUT_AVAILABLE:
            return None
        # Named special key?
        named = getattr(pynput_keyboard.Key, key, None)
        if named is not None:
            return named
        # Single printable character
        if len(key) == 1:
            return key
        return None
