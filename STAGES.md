# Stage-Wise Project Split 📋

This document describes how **Gesture UI Control** is built in three self-contained
stages.  Each stage is runnable on its own and forms the foundation for the next.

---

## Stage 1 — Gesture Detection Core 🖐️

**Goal:** Detect hand gestures from a webcam and print results to the terminal.
No mouse, no keyboard, no web UI.

### What's included

| File | Role |
|---|---|
| `gesture_control/config.py` | Config dataclass + load/save |
| `gesture_control/gesture_detector.py` | MediaPipe hand tracking & gesture classification |
| `stages/stage1_gesture_detection.py` | Stage 1 standalone runner |

### How to run

```bash
python stages/stage1_gesture_detection.py
```

Prints detected gesture + confidence to the console at ~30 fps.
Press **q** in the OpenCV preview window (or **Ctrl+C**) to quit.

### Gestures supported at this stage

All 10 gesture types are detected and labelled:
`none`, `pinch`, `thumbs_up`, `peace_sign`, `fist`, `open_palm`,
`ok_sign`, `pointing_up`, `scroll_up`, `scroll_down`

---

## Stage 2 — System Control (Mouse + Keyboard) 🖱️⌨️

**Goal:** Wire gesture detection to real mouse and keyboard actions on the host OS.

### What's added on top of Stage 1

| File | Role |
|---|---|
| `gesture_control/mouse_controller.py` | Cursor movement + click + scroll via pyautogui |
| `gesture_control/keyboard_controller.py` | Key presses via pynput |
| `stages/stage2_system_control.py` | Stage 2 standalone runner |

### Gesture → action mapping

| Gesture | Action |
|---|---|
| Hand movement | Move cursor (exponential smoothing) |
| Pinch | Left click |
| Scroll Up | Scroll wheel up / Page Up |
| Scroll Down | Scroll wheel down / Page Down |
| Thumbs Up | Media Play/Pause |
| Fist | Media Stop |

### How to run

```bash
python stages/stage2_system_control.py
```

Press **q** in the preview window to quit.

> **Note:** Mouse/keyboard control can be toggled in `config.json` via
> `enable_mouse_control` and `enable_keyboard_control`.

---

## Stage 3 — Web Dashboard (Full Application) 🌐

**Goal:** Expose everything through a browser-based live dashboard with a real-time
MJPEG video feed, gesture history log, and settings panel.

### What's added on top of Stage 2

| File | Role |
|---|---|
| `app.py` | Flask + SocketIO web server |
| `templates/index.html` | Single-page dark-theme dashboard |
| `static/css/style.css` | Dashboard styles |
| `static/js/app.js` | Client-side SocketIO + UI logic |

### How to run

```bash
python app.py
```

Open **http://localhost:5000** in your browser and press **▶ Start**.

### Extra features at this stage

- Live MJPEG video feed at `/video_feed`
- Real-time gesture events pushed via SocketIO (`gesture_event`)
- Gesture history log (last 20 events)
- Settings panel — edit all config values without touching `config.json`
- `GET /api/status`, `GET/POST /api/config`, `GET /api/gestures`, `GET /api/history`

---

## Stage Comparison

| Feature | Stage 1 | Stage 2 | Stage 3 |
|---|:---:|:---:|:---:|
| Hand landmark detection | ✅ | ✅ | ✅ |
| Gesture classification (10 types) | ✅ | ✅ | ✅ |
| OpenCV preview window | ✅ | ✅ | — |
| Mouse control | — | ✅ | ✅ |
| Keyboard control | — | ✅ | ✅ |
| Flask web server | — | — | ✅ |
| Live MJPEG stream | — | — | ✅ |
| SocketIO real-time events | — | — | ✅ |
| Settings panel | — | — | ✅ |

---

## Dependencies per Stage

```
Stage 1:  mediapipe  opencv-python  numpy
Stage 2:  + pyautogui  pynput
Stage 3:  + flask  flask-socketio  Pillow  python-dotenv
```

Full list: `requirements.txt`

---

## Running the Tests

Tests cover all three stages and run without a real camera or MediaPipe:

```bash
pip install pytest numpy
pytest tests/ -v
```
