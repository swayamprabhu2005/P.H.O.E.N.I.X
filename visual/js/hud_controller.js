/**
 * HUD Controller (v3.1)
 * Connects the HTML/CSS HUD overlay with Three.js PhoenixCore and the Python PyWebView API.
 * Features 100% transparent floating holographic HUD with on-demand disambiguation dialog.
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Three.js 3D Holographic Core
    const phoenixCore = new PhoenixCore('canvas-container');

    // DOM Elements
    const canvasContainer = document.getElementById('canvas-container');
    const wakeHint = document.getElementById('wake-hint');
    const confirmCard = document.getElementById('confirmation-card');
    const dialogPrompt = document.getElementById('dialog-prompt');
    const dialogTarget = document.getElementById('dialog-target');
    const dialogInput = document.getElementById('dialog-input');
    const btnYes = document.getElementById('btn-dialog-yes');
    const btnNo = document.getElementById('btn-dialog-no');

    const onboardCard = document.getElementById('onboarding-card');
    const onboardNameInput = document.getElementById('onboard-name-input');
    const onboardGroqInput = document.getElementById('onboard-groq-input');
    const onboardStatus = document.getElementById('onboard-status');
    const btnOnboardSubmit = document.getElementById('btn-onboard-submit');
    const btnOnboardClose = document.getElementById('btn-onboard-close');

    const guideCard = document.getElementById('guide-card');
    const btnGuideClose = document.getElementById('btn-guide-close');
    const btnGuideDone = document.getElementById('btn-guide-done');
    const btnGuideHelp = document.getElementById('btn-guide-help');

    let currentActionType = '';
    let currentActionData = {};
    let currentState = 'standby';

    // 2. Click 3D Core to Wake / Toggle Sleep
    let clickTimeout = null;
    canvasContainer.addEventListener('click', (e) => {
        // Ignore if clicking any dialog card
        if ((confirmCard && confirmCard.contains(e.target)) ||
            (onboardCard && onboardCard.contains(e.target)) ||
            (guideCard && guideCard.contains(e.target))) return;

        if (window.pywebview && window.pywebview.api) {
            if (currentState === 'standby') {
                window.pywebview.api.wake_up();
            } else {
                window.pywebview.api.go_to_sleep();
            }
        }
    });

    // Right-click core to hide to tray
    canvasContainer.addEventListener('contextmenu', (e) => {
        e.preventDefault();
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.hide_window();
        }
    });

    // 3. Holographic Disambiguation Dialog Handlers
    function submitDialog(confirmed) {
        if (!confirmed) {
            if (window.pywebview && window.pywebview.api && window.pywebview.api.confirm_action) {
                window.pywebview.api.confirm_action(false, '', currentActionType, JSON.stringify(currentActionData));
            }
            window.hideConfirmationDialog();
            return;
        }

        const typed = dialogInput.value.trim();
        const finalText = typed ? typed : dialogTarget.textContent.trim();

        if (window.pywebview && window.pywebview.api && window.pywebview.api.confirm_action) {
            window.pywebview.api.confirm_action(true, finalText, currentActionType, JSON.stringify(currentActionData));
        }
        window.hideConfirmationDialog();
    }

    btnYes.addEventListener('click', (e) => {
        e.stopPropagation();
        submitDialog(true);
    });

    btnNo.addEventListener('click', (e) => {
        e.stopPropagation();
        submitDialog(false);
    });

    dialogInput.addEventListener('keydown', (e) => {
        e.stopPropagation();
        if (e.key === 'Enter') {
            submitDialog(true);
        } else if (e.key === 'Escape') {
            submitDialog(false);
        }
    });

    // 4. Onboarding & Settings Dialog Handlers
    function getSelectedVoiceEngine() {
        const checked = document.querySelector('input[name="voice-engine"]:checked');
        return checked ? checked.value : 'vosk';
    }

    function submitOnboarding() {
        const nameVal = onboardNameInput.value.trim();
        const groqVal = onboardGroqInput.value.trim();
        const voiceEngine = getSelectedVoiceEngine();

        if (btnOnboardSubmit) btnOnboardSubmit.disabled = true;
        if (onboardStatus) {
            onboardStatus.style.color = '#6A0DAD';
            onboardStatus.textContent = 'Syncing voice model & saving...';
        }

        if (window.pywebview && window.pywebview.api && window.pywebview.api.complete_onboarding) {
            window.pywebview.api.complete_onboarding(nameVal, groqVal, voiceEngine);
        } else {
            window.hideOnboarding();
        }
    }

    if (btnOnboardClose) {
        btnOnboardClose.addEventListener('click', (e) => {
            e.stopPropagation();
            window.hideOnboarding();
        });
    }

    if (btnGuideClose) {
        btnGuideClose.addEventListener('click', (e) => {
            e.stopPropagation();
            window.hideGuide();
        });
    }

    if (btnGuideDone) {
        btnGuideDone.addEventListener('click', (e) => {
            e.stopPropagation();
            window.hideGuide();
        });
    }

    if (btnGuideHelp) {
        btnGuideHelp.addEventListener('click', (e) => {
            e.stopPropagation();
            window.hideGuide();
            window.showOnboarding(onboardNameInput ? onboardNameInput.value : '', getSelectedVoiceEngine(), true);
        });
    }

    if (btnOnboardSubmit) {
        btnOnboardSubmit.addEventListener('click', (e) => {
            e.stopPropagation();
            submitOnboarding();
        });
    }

    if (onboardNameInput) {
        onboardNameInput.addEventListener('keydown', (e) => {
            e.stopPropagation();
            if (e.key === 'Enter') {
                if (onboardGroqInput) onboardGroqInput.focus();
                else submitOnboarding();
            }
        });
    }

    if (onboardGroqInput) {
        onboardGroqInput.addEventListener('keydown', (e) => {
            e.stopPropagation();
            if (e.key === 'Enter') {
                submitOnboarding();
            }
        });
    }

    // 4. Global API exposed for Python to call
    window.updateState = function(state, message, activePath) {
        currentState = state;
        phoenixCore.setState(state);

        if (state === 'listening' || state === 'processing' || state === 'executing' || state === 'awaiting_confirmation') {
            document.body.classList.remove('sleep-mode');
            if (wakeHint) wakeHint.classList.add('hidden');
        } else if (state === 'standby') {
            document.body.classList.add('sleep-mode');
        }
    };

    window.showFeedback = function(cmdText, resultText, isSuccess) {
        if (isSuccess) {
            phoenixCore.triggerSuccessShockwave();
        }
    };

    window.showConfirmationDialog = function(promptText, targetText, actionType, actionData) {
        currentActionType = actionType || '';
        currentActionData = actionData || {};

        dialogPrompt.textContent = promptText || 'Did you mean:';
        dialogTarget.textContent = targetText || '';
        dialogInput.value = '';

        confirmCard.classList.remove('hidden');
        confirmCard.style.display = 'flex';
        confirmCard.style.opacity = '1';
        confirmCard.style.pointerEvents = 'auto';

        // Auto-focus manual input
        setTimeout(() => {
            dialogInput.focus();
        }, 100);
    };

    window.hideConfirmationDialog = function() {
        confirmCard.classList.add('hidden');
        confirmCard.style.display = 'none';
        confirmCard.style.opacity = '0';
        confirmCard.style.pointerEvents = 'none';
        currentActionType = '';
        currentActionData = {};
    };

    window.showOnboarding = function(currentName, currentEngine, isReopen) {
        if (!onboardCard) return;
        window.hideGuide();
        if (onboardNameInput && currentName) onboardNameInput.value = currentName;
        if (currentEngine) {
            const radio = document.querySelector(`input[name="voice-engine"][value="${currentEngine}"]`);
            if (radio) radio.checked = true;
        }
        if (btnOnboardClose) {
            if (isReopen) btnOnboardClose.classList.remove('hidden');
            else btnOnboardClose.classList.add('hidden');
        }
        if (btnOnboardSubmit) btnOnboardSubmit.disabled = false;
        if (onboardStatus) {
            onboardStatus.style.color = '#6B7280';
            onboardStatus.textContent = 'Say "Help" anytime to re-open Settings.';
        }

        onboardCard.classList.remove('hidden');
        onboardCard.style.display = 'flex';
        onboardCard.style.opacity = '1';
        onboardCard.style.pointerEvents = 'auto';

        setTimeout(() => {
            if (onboardNameInput) onboardNameInput.focus();
        }, 150);
    };

    window.onOnboardingResult = function(success, message) {
        if (btnOnboardSubmit) btnOnboardSubmit.disabled = false;
        if (success) {
            window.hideOnboarding();
        } else if (onboardStatus) {
            onboardStatus.style.color = '#DC143C';
            onboardStatus.textContent = message || 'Could not configure voice model.';
        }
    };

    window.hideOnboarding = function() {
        if (!onboardCard) return;
        onboardCard.classList.add('hidden');
        onboardCard.style.display = 'none';
        onboardCard.style.opacity = '0';
        onboardCard.style.pointerEvents = 'none';
    };

    window.showGuide = function() {
        if (!guideCard) return;
        window.hideOnboarding();
        guideCard.classList.remove('hidden');
        guideCard.style.display = 'flex';
        guideCard.style.opacity = '1';
        guideCard.style.pointerEvents = 'auto';
    };

    window.hideGuide = function() {
        if (!guideCard) return;
        guideCard.classList.add('hidden');
        guideCard.style.display = 'none';
        guideCard.style.opacity = '0';
        guideCard.style.pointerEvents = 'none';
    };

    window.setAudioLevel = function(level) {
        phoenixCore.setAudioLevel(level);
    };

    // Set initial state as standby (sleep mode, Ultron blue)
    window.updateState('standby', 'Click core to wake up', 'C:\\');
});
