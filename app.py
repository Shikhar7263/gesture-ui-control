from flask import Flask, jsonify, request
import cv2
import mediapipe as mp
import pyautogui
import threading

app = Flask(__name__)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Dictionary to hold gesture functions
GESTURES = {\n    'pinch': perform_pinch_action,\n    'thumbs_up': perform_thumbs_up_action,\n    'peace_sign': perform_peace_sign_action,\n    'fist': perform_fist_action,\n    'palm': perform_palm_action,\n    'ok_sign': perform_ok_sign_action\n}

@app.route('/gesture', methods=['POST'])
def handle_gesture():
    data = request.get_json()
    gesture = data.get('gesture')
    if gesture in GESTURES:
        GESTURES[gesture]()  # Call the associated function
        return jsonify({'status': 'ok', 'gesture': gesture}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Unknown gesture'}), 400

def process_video():
    cap = cv2.VideoCapture(0)
    while True:
        ret, image = cap.read()
        if not ret:
            break
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = hands.process(image)
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Logic to identify gestures would go here
                pass
        # Add more processing as required
    cap.release()

# Example gesture actions

def perform_pinch_action():
    # Code to perform mouse click or any other action
    pass

def perform_thumbs_up_action():
    # Code to take a screenshot
    pass

def perform_peace_sign_action():
    # Code to zoom in/out
    pass

def perform_fist_action():
    # Code to close any open application
    pass

def perform_palm_action():
    # Code to lock computer
    pass


def perform_ok_sign_action():
    # Code to open a specific program
    pass

if __name__ == '__main__':
    threading.Thread(target=process_video).start()
    app.run(host='0.0.0.0', port=5000)