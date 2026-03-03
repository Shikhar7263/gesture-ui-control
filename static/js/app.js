/**
 * app.js – supplementary client-side utilities for Gesture UI Control.
 *
 * Core logic (SocketIO, start/stop, settings, history polling) lives inline
 * in templates/index.html so the page is self-contained.  This file provides
 * reusable helper functions that can be imported or referenced externally.
 */

/**
 * Format a gesture value string into a human-readable label.
 * @param {string} gestureValue - e.g. "thumbs_up"
 * @returns {string} e.g. "Thumbs Up"
 */
function formatGestureLabel(gestureValue) {
  return gestureValue
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Render a confidence percentage as a colored string.
 * @param {number} confidence - value in [0, 1]
 * @returns {string} e.g. "87%"
 */
function formatConfidence(confidence) {
  return Math.round(confidence * 100) + '%';
}

/**
 * Debounce a function call.
 * @param {Function} fn
 * @param {number} delayMs
 * @returns {Function}
 */
function debounce(fn, delayMs) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delayMs);
  };
}
