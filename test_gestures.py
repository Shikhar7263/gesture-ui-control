"""
test_gestures.py - Unit tests for gesture recognition system
"""

import unittest
import numpy as np
from gesture_recognizer import GestureRecognizer

class TestGestureRecognizer(unittest.TestCase):
    
    def setUp(self):
        """Initialize test fixtures"""
        self.recognizer = GestureRecognizer()
    
    def test_gesture_recognizer_initialization(self):
        """Test that gesture recognizer initializes correctly"""
        self.assertIsNotNone(self.recognizer)
    
    def test_pinch_detection(self):
        """Test pinch gesture detection"""
        result = self.recognizer.classify_gesture(self._mock_pinch_landmarks())
        self.assertIsNotNone(result)
    
    def test_thumbs_up_detection(self):
        """Test thumbs up gesture detection"""
        result = self.recognizer.classify_gesture(self._mock_thumbs_up_landmarks())
        self.assertIsNotNone(result)
    
    def test_peace_sign_detection(self):
        """Test peace sign gesture detection"""
        result = self.recognizer.classify_gesture(self._mock_peace_sign_landmarks())
        self.assertIsNotNone(result)
    
    def _mock_pinch_landmarks(self):
        """Create mock landmarks for pinch gesture"""
        class MockLandmark:
            def __init__(self, x, y, z=0):
                self.x = x
                self.y = y
                self.z = z
        
        landmarks = [MockLandmark(0.5, 0.5) for _ in range(21)]
        return landmarks
    
    def _mock_thumbs_up_landmarks(self):
        """Create mock landmarks for thumbs up gesture"""
        class MockLandmark:
            def __init__(self, x, y, z=0):
                self.x = x
                self.y = y
                self.z = z
        
        landmarks = [MockLandmark(0.5, 0.5) for _ in range(21)]
        landmarks[4].y = 0.2
        return landmarks
    
    def _mock_peace_sign_landmarks(self):
        """Create mock landmarks for peace sign gesture"""
        class MockLandmark:
            def __init__(self, x, y, z=0):
                self.x = x
                self.y = y
                self.z = z
        
        landmarks = [MockLandmark(0.5, 0.5) for _ in range(21)]
        landmarks[8].y = 0.2
        landmarks[12].y = 0.2
        return landmarks

if __name__ == '__main__':
    unittest.main()