"""Configuration management for the Gesture Control system."""

import json
import os
from dataclasses import dataclass, asdict


CONFIG_FILE = "config.json"


@dataclass
class Config:
    """System-wide configuration settings."""

    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    min_detection_confidence: float = 0.7
    min_tracking_confidence: float = 0.7
    mouse_smoothing: float = 0.5
    click_cooldown: float = 0.3      # seconds between clicks
    gesture_cooldown: float = 0.5    # seconds between gesture triggers
    scroll_speed: int = 3
    enable_mouse_control: bool = True
    enable_keyboard_control: bool = True
    screen_margin: int = 50


def load_config() -> Config:
    """Load configuration from config.json if it exists, otherwise return defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Only apply keys that exist in Config; ignore unknown keys
            valid_keys = Config.__dataclass_fields__.keys()
            filtered = {k: v for k, v in data.items() if k in valid_keys}
            return Config(**filtered)
        except (json.JSONDecodeError, TypeError, KeyError):
            pass
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(asdict(config), f, indent=2)
