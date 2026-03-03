# Gesture UI Control 🖐️

An AI-powered, hand-gesture-based UI Control System that lets you control your mouse,
keyboard, and browser interface entirely through hand gestures captured via a webcam.
Built with MediaPipe, OpenCV, Flask, and SocketIO.

---

## ✨ Features

- **Real-time hand tracking** via MediaPipe Hands (single hand, ~30 fps)
- **10 gesture types**: Open Palm, Fist, Pinch, Thumbs Up, Peace Sign, OK Sign, Pointing Up, Scroll Up/Down, None
- **Mouse control**: cursor movement with exponential smoothing, left/right/double click, scroll
- **Keyboard control**: gesture-to-keystroke mappings (e.g. Thumbs Up → Play/Pause)
- **Live web dashboard**: MJPEG video feed, gesture status, history log, and settings panel
- **Headless-safe**: Flask server runs without a display; camera shows a placeholder frame when unavailable
- **Configurable**: all parameters editable via the web UI or `config.json`

---

## 🖥️ System Requirements

| Item | Minimum |
|---|---|
| Python | 3.9 + |
| Webcam | Any USB/built-in camera |
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 |
| RAM | 4 GB |

---

## 📦 Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/gesture-ui-control.git
cd gesture-ui-control

# 2. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 🚀 Quick Start

```bash
python app.py
```

Open **http://localhost:5000** in your browser, then press **▶ Start** to begin gesture
detection.  Point your camera at your hand and the system will recognise gestures in
real time.

---

## 🤚 Gesture Reference

| Gesture | Hand Shape | Action |
|---|---|---|
| **Open Palm** | All 5 fingers extended | — (reference pose) |
| **Fist** | All fingers curled | Stop media |
| **Pinch** | Thumb + index tips touching (< 0.05 normalized distance) | Left click |
| **Thumbs Up** | Only thumb extended upward | Play / Pause media |
| **Peace Sign** | Index + middle fingers up | — |
| **OK Sign** | Thumb + index circle, other fingers extended | Double click |
| **Pointing Up** | Only index finger extended | — |
| **Scroll Up** | Index + middle raised high (wrist low) | Scroll / Page Up |
| **Scroll Down** | Ring + pinky up, index + middle down | Scroll / Page Down |

---

## ⚙️ Configuration

Settings are stored in `config.json` (auto-created on first save).  You can edit them
through the **Settings** panel in the web UI or directly in the file.

| Parameter | Default | Description |
|---|---|---|
| `camera_index` | `0` | OpenCV camera index |
| `frame_width` | `640` | Capture width in pixels |
| `frame_height` | `480` | Capture height in pixels |
| `min_detection_confidence` | `0.7` | MediaPipe detection threshold |
| `min_tracking_confidence` | `0.7` | MediaPipe tracking threshold |
| `mouse_smoothing` | `0.5` | Exponential smoothing factor (0 = off, 0.99 = max) |
| `click_cooldown` | `0.3` | Seconds between successive clicks |
| `gesture_cooldown` | `0.5` | Seconds between successive gesture key triggers |
| `scroll_speed` | `3` | Scroll-wheel clicks per gesture |
| `enable_mouse_control` | `true` | Toggle mouse actions on/off |
| `enable_keyboard_control` | `true` | Toggle keyboard actions on/off |
| `screen_margin` | `50` | Pixel margin around screen edge for cursor mapping |

---

## 🏗️ Architecture

```
gesture-ui-control/
├── app.py                          # Flask + SocketIO web server
├── requirements.txt
├── config.json                     # Auto-generated runtime config
├── gesture_control/
│   ├── __init__.py
│   ├── config.py                   # Config dataclass + load/save helpers
│   ├── gesture_detector.py         # MediaPipe hand tracking & gesture logic
│   ├── mouse_controller.py         # pyautogui mouse actions + smoothing
│   └── keyboard_controller.py      # pynput keyboard actions
├── templates/
│   └── index.html                  # Single-page dashboard (dark theme)
├── static/
│   ├── css/style.css
│   └── js/app.js
└── tests/
    ├── __init__.py
    └── test_gesture_detector.py    # pytest test suite (no camera required)
```

**Request flow:**

1. Browser opens `http://localhost:5000/` → `index.html`
2. User clicks **Start** → `POST /api/start` → camera opens, background thread starts
3. Background thread calls `GestureDetector.process_frame()` each ~33 ms
4. Detected gesture emitted via SocketIO `gesture_event` → UI updates in real time
5. `GET /video_feed` serves an MJPEG stream rendered in the `<img>` tag
6. Mouse / keyboard actions are applied on the host machine via pyautogui / pynput

---

## 🗺️ Stage-Wise Development

The project is built in three progressive stages — each runnable on its own:

| Stage | Entry point | What it does |
|---|---|---|
| **Stage 1** — Gesture Detection | `stages/stage1_gesture_detection.py` | MediaPipe hand tracking + console output |
| **Stage 2** — System Control | `stages/stage2_system_control.py` | Stage 1 + mouse & keyboard automation |
| **Stage 3** — Web Dashboard | `app.py` | Stage 2 + Flask web UI + live video + SocketIO |

See **[STAGES.md](STAGES.md)** for the full breakdown, feature comparison table, and per-stage dependency list.

---

## 🧪 Running Tests

```bash
pip install pytest numpy
pytest tests/ -v
```

All 43 tests run without a real camera or MediaPipe install (heavy dependencies are
stubbed automatically).

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| *"Camera not available"* overlay | Check `camera_index` in settings; try `1` or `2` |
| High CPU usage | Lower `frame_width`/`frame_height` in config |
| Gestures not detected | Improve lighting; increase `min_detection_confidence` |
| Mouse jumps erratically | Increase `mouse_smoothing` (closer to `0.9`) |
| pyautogui `FailSafeException` | Already disabled; if it persists, restart the server |
| Port 5000 in use | Set `PORT` env var: `PORT=5001 python app.py` |

---

## 📄 License

MIT © gesture-ui-control contributors
