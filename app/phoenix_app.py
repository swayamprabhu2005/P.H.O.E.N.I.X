import json
import os
import sys
import threading
import time
from typing import Optional

import webview

from app.state_manager import StateManager, AppState
from commands.navigator import SystemNavigator
from commands.parser import CommandParser
from execution.executor import CommandExecutor
from voice.tts_engine import TTSEngine
from voice.vosk_recognizer import VoskVoiceRecognizer
from desktop.window_manager import DesktopWindowManager
from desktop.tray_manager import SystemTrayManager

class PhoenixApp:
    """Master application coordinator for P.H.O.E.N.I.X."""

    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config = self._load_config()

        # State & Navigator
        self.state_mgr = StateManager(AppState.STANDBY)
        self.navigator = SystemNavigator()

        # Commands & Execution
        self.parser = CommandParser()
        self.executor = CommandExecutor(navigator=self.navigator)

        # Voice Synthesis (Windows SAPI5)
        tts_cfg = self.config.get("assistant", {})
        self.tts = TTSEngine(
            enabled=tts_cfg.get("tts_enabled", True),
            rate=tts_cfg.get("tts_rate", 185),
            volume=tts_cfg.get("tts_volume", 1.0)
        )

        # Desktop Window & Tray
        win_cfg = self.config.get("window", {})
        self.window_mgr = DesktopWindowManager(
            on_wake=self.wake_up,
            on_sleep=self.go_to_sleep,
            on_hide=self.hide_to_tray,
            on_change_name=self.set_user_name,
            width=win_cfg.get("width", 380),
            height=win_cfg.get("height", 430)
        )

        self.tray_mgr = SystemTrayManager(
            on_show=self.show_window,
            on_hide=self.hide_to_tray,
            on_wake=self.wake_up,
            on_sleep=self.go_to_sleep,
            on_exit=self.shutdown
        )

        # Voice Recognition (Vosk) - Points strictly to local project models directory
        voice_cfg = self.config.get("voice", {})
        model_path = os.path.join(self.base_dir, "models", "vosk-model-small-en-us-0.15")

        self.recognizer = VoskVoiceRecognizer(
            model_path=model_path,
            sample_rate=voice_cfg.get("sample_rate", 16000),
            silence_timeout=voice_cfg.get("silence_timeout_seconds", 1.2),
            on_text_recognized=self.on_text_recognized,
            on_partial=self.on_partial_recognized
        )

        self._running = True

    def _load_config(self) -> dict:
        config_path = os.path.join(self.base_dir, "config", "settings.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_user_name(self) -> str:
        return self.config.get("user", {}).get("name", "Swayam")

    def set_user_name(self, new_name: str):
        cleaned = new_name.strip().title()
        if not cleaned:
            return
        if "user" not in self.config:
            self.config["user"] = {}
        self.config["user"]["name"] = cleaned
        config_path = os.path.join(self.base_dir, "config", "settings.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            self.tts.speak(f"Understood. I will address you as {cleaned}.")
        except Exception as e:
            print(f"Error saving name: {e}")

    def start(self):
        """Launches tray icon and starts pywebview GUI loop."""
        self.tray_mgr.start()
        self.window_mgr.create_window()

        # Run webview GUI loop (blocking main thread)
        webview.start(self._on_webview_ready, gui="edgechromium")

    def _on_webview_ready(self):
        """Called once the pywebview window is loaded."""
        time.sleep(0.5)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("standby", "Click 3D core to wake up", curr_dir)

        # Greet user personalized on launch: "At your service, Swayam."
        user_name = self.get_user_name()
        self.tts.speak(f"At your service, {user_name}.")

    def wake_up(self):
        """Awakens assistant upon clicking the 3D core and starts voice capture."""
        if self.state_mgr.current_state == AppState.LISTENING:
            return

        self.state_mgr.transition_to(AppState.LISTENING)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("listening", "Listening for command...", curr_dir)

        # Greet user personalized on wake up: "At your service, Swayam."
        user_name = self.get_user_name()
        self.tts.speak(f"At your service, {user_name}.")

        # Activate offline microphone
        self.recognizer.start_listening()

    def go_to_sleep(self):
        """Puts assistant to standby and releases microphone."""
        self.recognizer.stop_listening()
        self.state_mgr.transition_to(AppState.STANDBY)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("standby", "Entering standby...", curr_dir)
        self.tts.speak("Entering standby.")

    def hide_to_tray(self):
        """Hides the floating window to tray."""
        self.window_mgr.hide()

    def show_window(self):
        """Restores floating window from tray."""
        self.window_mgr.show()

    def shutdown(self):
        """Clean application shutdown."""
        self._running = False
        self.tts.speak("Shutting down Phoenix.")
        self.recognizer.stop_listening()
        self.tray_mgr.stop()
        self.window_mgr.destroy()
        sys.exit(0)

    def on_partial_recognized(self, partial_text: str):
        """Streams live recognized speech onto HUD."""
        if self.state_mgr.current_state == AppState.LISTENING and partial_text:
            curr_dir = self.navigator.get_current_directory()
            self.window_mgr.update_ui_state("listening", f'"{partial_text}..."', curr_dir)

    def on_text_recognized(self, recognized_text: str):
        """Processes finalized spoken sentence."""
        print(f"[RECOGNIZED]: {recognized_text}", flush=True)

        self.state_mgr.transition_to(AppState.PROCESSING)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("processing", f'Processing: "{recognized_text}"', curr_dir)

        # Parse command
        intent, params, feedback = self.parser.parse(recognized_text)

        if not intent:
            # Silent rejection: ignore ambient speech and non-registered phrases silently
            self.state_mgr.transition_to(AppState.LISTENING)
            curr_dir = self.navigator.get_current_directory()
            self.window_mgr.update_ui_state("listening", "Listening for command...", curr_dir)
            return

        # Special lifecycle commands
        if intent == "GO_TO_SLEEP":
            self.go_to_sleep()
            return
        elif intent == "SHUTDOWN":
            self.shutdown()
            return

        # Execute command
        self.state_mgr.transition_to(AppState.EXECUTING)
        success, display_msg, speech_text = self.executor.execute(intent, params, feedback)

        # Reload config in case name was changed
        self.config = self._load_config()

        # Update HUD
        new_dir = self.navigator.get_current_directory()
        self.window_mgr.show_feedback(recognized_text, display_msg, success)
        self.window_mgr.update_ui_state("listening", display_msg, new_dir)

        # Assistant vocal confirmation
        if speech_text:
            self.tts.speak(speech_text)

        # Return to listening state
        self.state_mgr.transition_to(AppState.LISTENING)
