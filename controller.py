import pyautogui
import time
from pynput import keyboard

class MouseKeyboardController:
    def __init__(self, sensitivity=1.0):
        self.sensitivity = sensitivity

    def smooth_move(self, x, y, duration=0.5):
        start_x, start_y = pyautogui.position()
        steps = int(duration * 100)
        for i in range(steps + 1):
            current_x = start_x + (x - start_x) * (i / steps)
            current_y = start_y + (y - start_y) * (i / steps)
            pyautogui.moveTo(current_x, current_y)
            time.sleep(duration / steps * self.sensitivity)

    def click(self, button='left'):  # 'left', 'right', 'middle'
        pyautogui.click(button=button)

    def double_click(self):
        pyautogui.doubleClick()

    def drag(self, x, y, duration=0.5):
        pyautogui.dragTo(x, y, duration=duration)

    def press_key(self, key):
        pyautogui.press(key)

    def hold_key(self, key):
        pyautogui.keyDown(key)

    def release_key(self, key):
        pyautogui.keyUp(key)

    def simulate_key_combination(self, *keys):
        pyautogui.hotkey(*keys)

# Example usage:
# controller = MouseKeyboardController(sensitivity=1.5)
# controller.smooth_move(100, 200)
# controller.click('right')
# controller.double_click()
# controller.drag(300, 400)
# controller.press_key('a')
# controller.simulate_key_combination('ctrl', 'c')