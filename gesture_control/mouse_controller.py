"""Mouse control using pyautogui with smoothing and cooldown."""

import time
from typing import Tuple

try:
    import pyautogui
    # FAILSAFE is intentionally disabled: the gesture system deliberately moves
    # the cursor to screen corners, which would otherwise trigger the pyautogui
    # FailSafeException and crash the controller.
    pyautogui.FAILSAFE = False
    _PYAUTOGUI_AVAILABLE = True
except ImportError:
    _PYAUTOGUI_AVAILABLE = False

from gesture_control.config import Config


class MouseController:
    """Maps hand position to screen coordinates and simulates mouse actions."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._prev_x: float = 0.0
        self._prev_y: float = 0.0
        self._last_click_time: float = 0.0

        if _PYAUTOGUI_AVAILABLE:
            screen_w, screen_h = pyautogui.size()
            self._prev_x = screen_w / 2.0
            self._prev_y = screen_h / 2.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def move_cursor(self, hand_center: Tuple[float, float], frame_size: Tuple[int, int]) -> None:
        """Map normalised hand_center (0-1 range) to screen coordinates.

        Applies exponential smoothing controlled by ``config.mouse_smoothing``.
        """
        if not _PYAUTOGUI_AVAILABLE or not self._config.enable_mouse_control:
            return

        screen_w, screen_h = pyautogui.size()
        margin = self._config.screen_margin

        # Flip x-axis so that moving hand left moves cursor left (mirror mode)
        norm_x = 1.0 - hand_center[0]
        norm_y = hand_center[1]

        # Map to screen space with margin
        target_x = margin + norm_x * (screen_w - 2 * margin)
        target_y = margin + norm_y * (screen_h - 2 * margin)

        # Exponential smoothing
        alpha = 1.0 - self._config.mouse_smoothing
        smooth_x = alpha * target_x + (1.0 - alpha) * self._prev_x
        smooth_y = alpha * target_y + (1.0 - alpha) * self._prev_y

        self._prev_x = smooth_x
        self._prev_y = smooth_y

        try:
            pyautogui.moveTo(int(smooth_x), int(smooth_y), duration=0)
        except Exception:
            pass

    def left_click(self) -> bool:
        """Perform a left click if cooldown has elapsed. Returns True on success."""
        return self._click("left")

    def right_click(self) -> bool:
        """Perform a right click if cooldown has elapsed. Returns True on success."""
        return self._click("right")

    def double_click(self) -> bool:
        """Perform a double click if cooldown has elapsed. Returns True on success."""
        if not _PYAUTOGUI_AVAILABLE or not self._config.enable_mouse_control:
            return False
        if time.time() - self._last_click_time < self._config.click_cooldown:
            return False
        try:
            pyautogui.doubleClick()
            self._last_click_time = time.time()
            return True
        except Exception:
            return False

    def scroll(self, direction: str, amount: int = 0) -> None:
        """Scroll the mouse wheel.

        Args:
            direction: ``"up"`` or ``"down"``.
            amount: Number of scroll clicks; defaults to ``config.scroll_speed``.
        """
        if not _PYAUTOGUI_AVAILABLE or not self._config.enable_mouse_control:
            return
        clicks = amount if amount > 0 else self._config.scroll_speed
        delta = clicks if direction.lower() == "up" else -clicks
        try:
            pyautogui.scroll(delta)
        except Exception:
            pass

    def get_screen_size(self) -> Tuple[int, int]:
        """Return current screen dimensions as (width, height)."""
        if _PYAUTOGUI_AVAILABLE:
            return pyautogui.size()
        return (1920, 1080)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _click(self, button: str) -> bool:
        if not _PYAUTOGUI_AVAILABLE or not self._config.enable_mouse_control:
            return False
        if time.time() - self._last_click_time < self._config.click_cooldown:
            return False
        try:
            pyautogui.click(button=button)
            self._last_click_time = time.time()
            return True
        except Exception:
            return False
