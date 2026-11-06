import json
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from typing import Optional, Dict, Any

import webview

from ai.groq_client import GroqClient
from app.state_manager import StateManager, AppState
from commands.navigator import SystemNavigator
from commands.parser import CommandParser
from execution.executor import CommandExecutor
from memory.memory_manager import MemoryManager
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

        # Commands, Memory & AI
        self.parser = CommandParser()
        self.executor = CommandExecutor(navigator=self.navigator)
        self.memory_mgr = MemoryManager()

        # Groq Intelligence Client
        ai_cfg = self.config.get("ai", {})
        self.groq_client = GroqClient(
            api_key=ai_cfg.get("groq_api_key", ""),
            model=ai_cfg.get("groq_model", "llama-3.3-70b-versatile")
        )

        # Pending confirmation state for unconstrained disambiguation
        self._pending_confirmation: Optional[Dict[str, Any]] = None

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
            on_confirm_action=self.on_gui_confirm_action,
            on_save_groq_key=self.set_groq_key,
            on_onboarding_complete=self.on_onboarding_complete,
            on_close=self.shutdown,
            width=win_cfg.get("width", 380),
            height=win_cfg.get("height", 420)
        )

        self.tray_mgr = SystemTrayManager(
            on_show=self.show_window,
            on_hide=self.hide_to_tray,
            on_wake=self.wake_up,
            on_sleep=self.go_to_sleep,
            on_exit=self.shutdown
        )

        # Build constrained grammar from command registry + memory phrases
        combined_phrases = self._build_grammar_phrases()

        # Voice Recognition (Vosk)
        voice_cfg = self.config.get("voice", {})
        model_path = os.path.join(self.base_dir, "models", "vosk-model-small-en-us-0.15")

        self.recognizer = VoskVoiceRecognizer(
            model_path=model_path,
            sample_rate=voice_cfg.get("sample_rate", 16000),
            silence_timeout=voice_cfg.get("silence_timeout_seconds", 1.2),
            energy_threshold=voice_cfg.get("energy_threshold", 250.0),
            grammar_phrases=combined_phrases,
            on_text_recognized=self.on_text_recognized,
            on_partial=self.on_partial_recognized
        )

        self._running = True

    def _build_grammar_phrases(self) -> list:
        phrases = set(self.parser.get_grammar_phrases())
        phrases.update(self.memory_mgr.get_known_phrases())
        return sorted(list(phrases))

    def _load_config(self) -> dict:
        config_path = os.path.join(self.base_dir, "config", "settings.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_user_name(self) -> str:
        return self.config.get("user", {}).get("name", "").strip() or "Operator"

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

    def set_groq_key(self, api_key: str):
        cleaned = api_key.strip()
        if not cleaned:
            return
        if "ai" not in self.config:
            self.config["ai"] = {}
        self.config["ai"]["groq_api_key"] = cleaned
        self.groq_client.set_api_key(cleaned)
        config_path = os.path.join(self.base_dir, "config", "settings.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            self.tts.speak("Groq API key configured successfully.")
        except Exception as e:
            print(f"Error saving Groq key: {e}")

    def start(self):
        """Launches tray icon and starts pywebview GUI loop."""
        self.tray_mgr.start()
        self.window_mgr.create_window()

        # Pass high-res multi-resolution icon to pywebview so Windows taskbar displays official logo
        ico_path = os.path.join(self.base_dir, "assets", "phoenix.ico")

        # Run webview GUI loop (blocking main thread)
        webview.start(self._on_webview_ready, gui="edgechromium", icon=ico_path)

    def on_onboarding_complete(self, name: str, groq_key: str):
        chosen_name = name.strip().title() if name.strip() else "Operator"
        chosen_key = groq_key.strip()

        if "user" not in self.config:
            self.config["user"] = {}
        self.config["user"]["name"] = chosen_name

        if "ai" not in self.config:
            self.config["ai"] = {}
        self.config["ai"]["groq_api_key"] = chosen_key
        if chosen_key:
            self.groq_client.set_api_key(chosen_key)

        config_path = os.path.join(self.base_dir, "config", "settings.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

        # Write setup done marker
        marker_path = os.path.join(self.base_dir, "config", ".setup_done")
        try:
            with open(marker_path, "w", encoding="utf-8") as f:
                f.write(f"Setup completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception:
            pass

        self.tts.speak(f"Personalization complete. At your service, {chosen_name}.")

    def _on_webview_ready(self):
        """Called once the pywebview window is loaded. Starts silently in standby."""
        time.sleep(0.4)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("standby", "", curr_dir)

        setup_marker = os.path.join(self.base_dir, "config", ".setup_done")
        if not os.path.exists(setup_marker) or not self.config.get("user", {}).get("name"):
            self.window_mgr.show_onboarding()

        # Calibrate ambient microphone noise floor silently in background
        threading.Thread(target=self.recognizer.calibrate_ambient_noise, args=(0.4,), daemon=True).start()
        # Normal startup is completely silent. Only greets when clicked/activated.

    def wake_up(self):
        """Awakens assistant upon clicking the 3D core and starts voice capture."""
        if self.state_mgr.current_state == AppState.LISTENING:
            return

        self.state_mgr.transition_to(AppState.LISTENING)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("listening", "", curr_dir)

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
        self.window_mgr.hide_confirmation()
        self._pending_confirmation = None
        self.window_mgr.update_ui_state("standby", "", curr_dir)
        self.tts.speak("Entering standby.")

    def hide_to_tray(self):
        self.window_mgr.hide()

    def show_window(self):
        self.window_mgr.show()

    def shutdown(self):
        if not self._running:
            return
        self._running = False

        try:
            self.recognizer.stop_listening()
        except Exception:
            pass

        try:
            self.tray_mgr.stop()
        except Exception:
            pass

        try:
            self.window_mgr.destroy()
        except Exception:
            pass

        # Speak shutdown feedback and cleanly terminate OS process
        try:
            self.tts.speak("Shutting down Phoenix.")
        except Exception:
            pass

        def _terminate():
            time.sleep(0.6)
            os._exit(0)

        threading.Thread(target=_terminate, daemon=True).start()

    def on_partial_recognized(self, partial_text: str):
        if self.state_mgr.current_state == AppState.LISTENING and partial_text:
            curr_dir = self.navigator.get_current_directory()
            self.window_mgr.update_ui_state("listening", f'"{partial_text}..."', curr_dir)

    def on_text_recognized(self, recognized_text: str):
        """Processes finalized spoken sentence."""
        print(f"[RECOGNIZED]: {recognized_text}", flush=True)

        # 1. Handle active disambiguation confirmation via voice
        if self._pending_confirmation:
            intent, _, _ = self.parser.parse(recognized_text)
            if intent == "CONFIRM_YES":
                action = self._pending_confirmation
                self._pending_confirmation = None
                self.window_mgr.hide_confirmation()
                self._execute_confirmed_action(action["target"], action["action_type"], action["action_data"])
                return
            elif intent == "CONFIRM_NO":
                self._pending_confirmation = None
                self.window_mgr.hide_confirmation()
                self.tts.speak("Cancelled. You may type manually or speak another command.")
                self.state_mgr.transition_to(AppState.LISTENING)
                return

        self.state_mgr.transition_to(AppState.PROCESSING)
        curr_dir = self.navigator.get_current_directory()
        self.window_mgr.update_ui_state("processing", "", curr_dir)

        # Parse command
        intent, params, feedback = self.parser.parse(recognized_text)

        if not intent:
            # Check if user spoke a website or search term directly (e.g. "chatgpt", "chatgpt.com")
            matched_site = self.memory_mgr.find_website_match(recognized_text)
            if matched_site:
                self._prompt_search_confirmation(matched_site["name"], matched_site["url"])
                return

            # Silent rejection: ignore ambient noise silently
            self.state_mgr.transition_to(AppState.LISTENING)
            self.window_mgr.update_ui_state("listening", "", curr_dir)
            return

        # Special lifecycle commands
        if intent == "WAKE_UP":
            self.wake_up()
            return
        elif intent == "GO_TO_SLEEP":
            self.go_to_sleep()
            return
        elif intent == "SHUTDOWN":
            self.shutdown()
            return

        # Handle unconstrained Web Search with Groq / Memory disambiguation
        if intent == "WEB_SEARCH":
            query = params.get("query", "").strip()
            self._handle_web_search_with_disambiguation(query)
            return

        # Handle unconstrained file/folder creation confirmation
        if intent in ["CREATE_FILE", "CREATE_FOLDER", "CREATE_TXT_FILE", "CREATE_WORD_FILE"]:
            name = params.get("name", "").strip()
            # If name is present, confirm with user so typos can be corrected manually
            self._prompt_file_confirmation(intent, name, params)
            return

        # Execute standard command
        self.state_mgr.transition_to(AppState.EXECUTING)
        success, display_msg, speech_text = self.executor.execute(intent, params, feedback)

        # Record website visits to memory for specialized modes
        if intent == "LEARNING_MODE_CHATGPT":
            self.memory_mgr.record_website("https://chatgpt.com", "ChatGPT")
        elif intent == "LEARNING_MODE_PERPLEXITY":
            self.memory_mgr.record_website("https://www.perplexity.ai", "Perplexity")

        # Reload config in case settings were changed
        self.config = self._load_config()

        # Update HUD
        new_dir = self.navigator.get_current_directory()
        self.window_mgr.show_feedback(recognized_text, display_msg, success)
        self.window_mgr.update_ui_state("listening", "", new_dir)

        # Assistant vocal confirmation
        if speech_text:
            self.tts.speak(speech_text)

        # Return to listening state
        self.state_mgr.transition_to(AppState.LISTENING)

    def _handle_web_search_with_disambiguation(self, raw_query: str):
        """Disambiguates web search using Memory and Groq before prompting user."""
        target_name = raw_query
        target_url = ""

        # 1. Check local memory
        matched_site = self.memory_mgr.find_website_match(raw_query)
        if matched_site:
            target_name = matched_site["name"]
            target_url = matched_site["url"]
        elif self.groq_client.is_available():
            # 2. Query Groq AI for smart disambiguation
            groq_res = self.groq_client.disambiguate_query(
                raw_query,
                self.memory_mgr.data.get("visited_websites"),
                self.memory_mgr.data.get("recent_searches")
            )
            if groq_res:
                target_name = groq_res.get("interpreted", target_name)
                if groq_res.get("is_url") and groq_res.get("target_url"):
                    target_url = groq_res.get("target_url")

        self._prompt_search_confirmation(target_name, target_url)

    def _prompt_search_confirmation(self, target_name: str, target_url: str = ""):
        """Prompts confirmation dialog with manual typing fallback."""
        prompt = "Did you mean to open:" if target_url else "Did you mean to search:"
        action_data = {"url": target_url, "query": target_name}

        self._pending_confirmation = {
            "action_type": "search",
            "target": target_name,
            "action_data": action_data
        }

        self.window_mgr.show_confirmation(prompt, target_name, "search", action_data)
        spoken_prompt = f"Did you mean to open {target_name}?" if target_url else f"Did you mean to search {target_name}?"
        self.tts.speak(spoken_prompt)

    def _prompt_file_confirmation(self, intent: str, name: str, params: dict):
        """Prompts confirmation for file or folder naming with manual typing fallback."""
        item_type = "folder" if "FOLDER" in intent else "file"
        prompt = f"Confirm {item_type} name:"

        self._pending_confirmation = {
            "action_type": intent,
            "target": name,
            "action_data": params
        }

        self.window_mgr.show_confirmation(prompt, name, intent, params)
        self.tts.speak(f"Is {name} the {item_type} name you intend to use?")

    def on_gui_confirm_action(self, confirmed: bool, manual_text: str, action_type: str, action_data: Dict[str, Any]):
        """Called directly when user clicks Yes / Cancel or submits manual text in dialog."""
        self._pending_confirmation = None
        self.window_mgr.hide_confirmation()

        if not confirmed:
            self.tts.speak("Cancelled.")
            self.state_mgr.transition_to(AppState.LISTENING)
            return

        target_text = manual_text.strip() if manual_text.strip() else action_data.get("query", "")
        self._execute_confirmed_action(target_text, action_type, action_data)

    def _execute_confirmed_action(self, target_text: str, action_type: str, action_data: Dict[str, Any]):
        """Executes the confirmed action (opening Chrome, searching, or creating files)."""
        self.state_mgr.transition_to(AppState.EXECUTING)

        if action_type == "search":
            url = action_data.get("url", "")
            # Check if user typed a specific URL or domain manually
            if target_text.startswith("http://") or target_text.startswith("https://"):
                url = target_text
            elif "." in target_text and " " not in target_text:
                url = f"https://{target_text}"

            if url:
                self.executor.app_launcher.launch("chrome")
                webbrowser.open(url)
                self.memory_mgr.record_website(url, target_text)
                self.tts.speak(f"Opening {target_text}.")
                self.window_mgr.show_feedback(target_text, f"Opened {url}", True)
            else:
                self.executor.app_launcher.launch("chrome")
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(target_text)}"
                webbrowser.open(search_url)
                self.memory_mgr.record_search(target_text)
                self.tts.speak(f"Searching for {target_text}.")
                self.window_mgr.show_feedback(target_text, f"Searched: {target_text}", True)

        elif action_type in ["CREATE_FILE", "CREATE_FOLDER", "CREATE_TXT_FILE", "CREATE_WORD_FILE"]:
            action_data["name"] = target_text
            success, display_msg, speech_text = self.executor.execute(action_type, action_data)
            self.memory_mgr.record_file(target_text)
            if speech_text:
                self.tts.speak(speech_text)
            self.window_mgr.show_feedback(target_text, display_msg, success)

        # Update grammar with new phrases in background
        self.recognizer.set_grammar(self._build_grammar_phrases())
        self.state_mgr.transition_to(AppState.LISTENING)
