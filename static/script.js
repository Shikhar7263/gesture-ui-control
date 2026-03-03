// static/script.js

// Function to handle webcam streaming via WebRTC
async function initWebcam() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const video = document.querySelector('video');
    video.srcObject = stream;
    video.play();
}

// Function to communicate with Flask backend
async function fetchGestureData() {
    try {
        const response = await fetch('http://localhost:5000/gesture'); // Adjust the URL as necessary
        const data = await response.json();
        updateUI(data);
    } catch (error) {
        console.error('Error fetching gesture data:', error);
    }
}

// Function to update the UI based on received gesture data
function updateUI(data) {
    const gestureDisplay = document.getElementById('gestureDisplay');
    gestureDisplay.innerText = `Detected Gesture: ${data.gesture}`;
}

// Function to manage user interactions
function setupUserInteractions() {
    const button = document.getElementById('actionButton');
    button.addEventListener('click', () => {
        console.log('User interacted with the button!');
        // Additional interaction logic here
    });
}

// Initialize functions on window load
window.onload = () => {
    initWebcam();
    setupUserInteractions();
    setInterval(fetchGestureData, 1000); // Fetch gesture data every second
};