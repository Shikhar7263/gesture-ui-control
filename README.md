# Gesture UI Control

## Installation Instructions

1. **Clone the repository**: 
   ```bash
   git clone https://github.com/Shikhar7263/gesture-ui-control.git
   cd gesture-ui-control
   ```
2. **Install dependencies**:
   ```bash
   npm install
   ```
3. **Run the application**:
   ```bash
   npm start
   ```

## Feature Documentation

- **Gesture Recognition**: Recognizes various gestures for controlling the UI.
- **Customizable Settings**: Allows user to customize gesture settings.
- **Real-time Feedback**: Provides immediate feedback on gesture recognition.
- **Multi-platform Support**: Works on various platforms (Windows, Mac, Linux).

## Usage Guide

To use the gesture control system, ensure that your camera is enabled and follow these steps:
   1. **Start the application**.
   2. **Allow camera access** when prompted.
   3. **Use the following gestures to interact with the UI**:
      - **Swipe Left**: Navigate to the previous screen.
      - **Swipe Right**: Navigate to the next screen.
      - **Pinch**: Zoom in/out.
      - **Wave**: Open menu.

## Gesture Descriptions

1. **Swipe Left**: Move your hand quickly to the left.
2. **Swipe Right**: Move your hand quickly to the right.
3. **Pinch**: Bring your thumb and index finger together or apart.
4. **Wave**: Move your hand side to side.

## API Endpoints

- **GET /api/gestures**: Retrieves a list of recognized gestures.
- **POST /api/gestures**: Adds a new custom gesture to the system.
- **DELETE /api/gestures/:id**: Deletes a specified gesture.

## Troubleshooting

- If gestures are not recognized:
  - Ensure your camera is properly positioned and turned on.
  - Check lighting conditions and adjust accordingly.
  - Restart the application if the issue persists.

## Stage Roadmap

**Q1 2026**: Initial release with basic gesture recognition.
**Q2 2026**: Implement customizable gestures and settings.
**Q3 2026**: Expand API functionality and add documentation.
**Q4 2026**: User feedback and optimization phase.