# config.py

# Gesture Control Configuration

# Sensitivity settings for gesture detection
GESTURE_SENSITIVITY = {
    'swipe': 0.7,    # Sensitivity for swipe gestures
    'tap': 0.5,      # Sensitivity for tap gestures
    'hold': 0.8      # Sensitivity for hold gestures
}

# Mouse speed settings
MOUSE_SPEED = 1.5  # Speed multiplier for mouse movement based on gestures

# Confidence thresholds for gesture recognition
CONFIDENCE_THRESHOLDS = {
    'swipe': 0.65,   # Threshold for swipe gestures
    'tap': 0.5,      # Threshold for tap gestures
    'hold': 0.75     # Threshold for hold gestures
}

# Other tunable parameters
OTHER_SETTINGS = {
    'max_gestures': 10,    # Maximum number of gestures that can be recognized
    'gesture_timeout': 2.0  # Time (in seconds) to wait for gesture recognition
}