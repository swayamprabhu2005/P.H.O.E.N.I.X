/**
 * HUD Controller (v3.0)
 * Connects the HTML/CSS HUD overlay with the Three.js PhoenixCore and the Python PyWebView API.
 * Supports smooth state transitions, awake (Amber) vs sleep (Ultron Blue) UI modes,
 * and click-to-wake interaction.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Three.js 3D Core
    const phoenixCore = new PhoenixCore('canvas-container');

    // DOM Elements
    const canvasContainer = document.getElementById('canvas-container');
    const statusDot = document.getElementById('status-dot');
    const statusBadge = document.getElementById('status-badge');
    const toastText = document.getElementById('toast-text');
    const pathIndicator = document.getElementById('path-indicator');
    const wakeHint = document.getElementById('wake-hint');
    const btnSleep = document.getElementById('btn-sleep');
    const btnClose = document.getElementById('btn-close');

    // 2. Click 3D Core to Wake Up
    canvasContainer.addEventListener('click', () => {
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.wake_up();
        } else {
            // Standalone browser preview fallback
            window.updateState('listening', 'Listening for command...', 'C:\\Users\\Desktop');
        }
    });

    // 3. Sleep / Standby Button
    btnSleep.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.go_to_sleep();
        } else {
            window.updateState('standby', 'Entering sleep mode...', 'C:\\Users\\Desktop');
        }
    });

    // 4. Hide Window (Minimize to tray)
    btnClose.addEventListener('click', (e) => {
        e.stopPropagation();
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.hide_window();
        }
    });

    // 5. Global API exposed for Python to call
    window.updateState = function(state, message, activePath) {
        phoenixCore.setState(state);

        statusBadge.textContent = state.toUpperCase();
        statusBadge.className = 'hud-status-badge ' + state;

        if (state === 'listening') {
            document.body.classList.remove('sleep-mode');
            statusDot.classList.add('active');
            wakeHint.classList.add('hidden');
        } else if (state === 'standby') {
            document.body.classList.add('sleep-mode');
            statusDot.classList.remove('active');
            wakeHint.classList.remove('hidden');
        } else if (state === 'processing') {
            document.body.classList.remove('sleep-mode');
            statusDot.classList.add('active');
            wakeHint.classList.add('hidden');
        }

        if (message) {
            toastText.textContent = message;
        }

        if (activePath) {
            pathIndicator.textContent = activePath;
        }
    };

    window.showFeedback = function(cmdText, resultText, isSuccess) {
        if (cmdText && resultText) {
            toastText.innerHTML = `<span class="toast-cmd">"${cmdText}"</span> &rarr; ${resultText}`;
        } else if (resultText) {
            toastText.textContent = resultText;
        }

        if (isSuccess) {
            phoenixCore.triggerSuccessShockwave();
        }
    };

    window.setAudioLevel = function(level) {
        phoenixCore.setAudioLevel(level);
    };

    // Set initial state as standby (sleep)
    window.updateState('standby', 'Click core to wake up', 'C:\\');
});
