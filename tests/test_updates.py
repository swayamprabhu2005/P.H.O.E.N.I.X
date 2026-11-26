import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from commands.parser import CommandParser
from execution.uia_ops import UIAutomator
from voice.audio_pipeline import AudioPipeline
from voice.tts_engine import TTSEngine


class TestAudioPipeline(unittest.TestCase):
    def test_tts_echo_gate_drops_frames(self):
        speaking = True
        pipeline = AudioPipeline(sample_rate=16000, tts_is_speaking=lambda: speaking)
        tone = (np.sin(2 * np.pi * 440 * np.arange(1000) / 16000) * 5000).astype(np.int16).tobytes()

        cleaned, is_speech, rms = pipeline.process_frame(tone)
        self.assertIsNone(cleaned)
        self.assertFalse(is_speech)
        self.assertEqual(rms, 0.0)

        speaking = False
        cleaned2, _, _ = pipeline.process_frame(tone)
        self.assertIsNotNone(cleaned2)

    def test_spectral_calibration_and_denoising(self):
        pipeline = AudioPipeline(sample_rate=16000)
        # Simulate steady 200 Hz fan hum during calibration
        t = np.arange(1000) / 16000.0
        hum = (np.sin(2 * np.pi * 200 * t) * 400).astype(np.int16)
        pipeline.calibrate_from_frames([hum, hum, hum])
        self.assertIsNotNone(pipeline._noise_profile)

        # Feed pure hum: should NOT trigger speech
        _, is_speech_hum, _ = pipeline.process_frame(hum.tobytes())
        self.assertFalse(is_speech_hum)

        # Feed 1000 Hz vocal-band signal above noise floor: should trigger speech
        voice = (np.sin(2 * np.pi * 1000 * t) * 6000).astype(np.int16)
        cleaned, is_speech_voice, _ = pipeline.process_frame(voice.tobytes())
        self.assertIsNotNone(cleaned)
        self.assertTrue(is_speech_voice)


class TestUIAutomator(unittest.TestCase):
    def test_blocks_destructive_clicks(self):
        uia = UIAutomator()
        ok, msg = uia.click_element("Delete Account")
        self.assertFalse(ok)
        self.assertIn("safety", msg.lower())

        ok2, msg2 = uia.click_element("Format Drive")
        self.assertFalse(ok2)
        self.assertIn("safety", msg2.lower())

    def test_fuzzy_element_matching(self):
        uia = UIAutomator()
        dummy_elem = object()
        elements = [("Save Document", dummy_elem), ("Cancel", object())]
        match = uia._find_best_element("save", elements)
        self.assertIsNotNone(match)
        self.assertEqual(match[0], "Save Document")


class TestUIACommandParsing(unittest.TestCase):
    def setUp(self):
        self.parser = CommandParser()

    def test_uia_commands(self):
        intent, params, _ = self.parser.parse("click submit")
        self.assertEqual(intent, "UIA_CLICK")
        self.assertEqual(params.get("element"), "submit")

        intent, params, _ = self.parser.parse("type hello world")
        self.assertEqual(intent, "UIA_TYPE")
        self.assertEqual(params.get("text"), "hello world")

        intent, _, _ = self.parser.parse("scroll window down")
        self.assertEqual(intent, "UIA_SCROLL_DOWN")

        intent, _, _ = self.parser.parse("scroll window up")
        self.assertEqual(intent, "UIA_SCROLL_UP")

        intent, params, _ = self.parser.parse("focus notepad")
        self.assertEqual(intent, "FOCUS_WINDOW")
        self.assertEqual(params.get("window"), "notepad")


class TestVoiceOnlyConfirmation(unittest.TestCase):
    def test_voice_only_confirmation_skips_text_dialog(self):
        from app.phoenix_app import PhoenixApp

        with patch.object(PhoenixApp, "__init__", lambda self: None):
            app = PhoenixApp()
            app.config = {"assistant": {"voice_only_confirmation": True}}
            app._pending_confirmation = None
            app._confirmation_timer = None
            app.navigator = MagicMock()
            app.navigator.get_current_directory.return_value = "C:\\"
            app.recognizer = MagicMock()
            app.window_mgr = MagicMock()
            app.tts = MagicMock()
            app.state_mgr = MagicMock()

            app._prompt_search_confirmation("ChatGPT", "https://chatgpt.com")

            app.window_mgr.show_confirmation.assert_not_called()
            app.window_mgr.hide_confirmation.assert_called_once()
            app.window_mgr.update_ui_state.assert_called_with("awaiting_confirmation", "", "C:\\")
            app.tts.speak.assert_called_with("Did you mean to open ChatGPT?")
            app._cancel_confirmation_timeout()


class TestPluggableVoiceAndGuide(unittest.TestCase):
    def test_help_guide_and_lock_pc_parsing(self):
        parser = CommandParser()
        self.assertEqual(parser.parse("help")[0], "OPEN_SETTINGS")
        self.assertEqual(parser.parse("guide")[0], "OPEN_GUIDE")
        self.assertEqual(parser.parse("lock the pc")[0], "LOCK_PC")

    def test_exclusive_voice_switch_and_validation(self):
        import os
        import tempfile
        import json
        from voice.engine_manager import switch_and_sync_engine

        with tempfile.TemporaryDirectory() as tmp:
            cfg_dir = os.path.join(tmp, "config")
            os.makedirs(cfg_dir, exist_ok=True)
            with open(os.path.join(cfg_dir, "settings.json"), "w", encoding="utf-8") as f:
                json.dump({"voice": {"engine": "vosk"}}, f)

            ok, _ = switch_and_sync_engine("unknown_model", tmp)
            self.assertFalse(ok)

            ok2, _ = switch_and_sync_engine("groq_whisper", tmp, groq_api_key="")
            self.assertFalse(ok2)

            with patch("voice.engine_manager.get_models_cache_dir", return_value=os.path.join(tmp, "cache")):
                cache_dir = os.path.join(tmp, "cache")
                old_model = os.path.join(cache_dir, "vosk-model-small-en-us-0.15")
                os.makedirs(old_model, exist_ok=True)

                ok3, _ = switch_and_sync_engine("windows_native", tmp)
                self.assertTrue(ok3)
                self.assertFalse(os.path.exists(old_model))

                with open(os.path.join(cfg_dir, "settings.json"), "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self.assertEqual(saved["voice"]["engine"], "windows_native")

    def test_lock_pc_triggers_auto_sleep(self):
        from app.phoenix_app import PhoenixApp

        with patch.object(PhoenixApp, "__init__", lambda self: None):
            app = PhoenixApp()
            app.config = {}
            app._pending_confirmation = None
            app._confirmation_timer = None
            app.navigator = MagicMock()
            app.navigator.get_current_directory.return_value = "C:\\"
            app.parser = CommandParser()
            app.executor = MagicMock()
            app.executor.execute.return_value = (True, "Locked workstation", "Workstation locked.")
            app.memory_mgr = MagicMock()
            app.window_mgr = MagicMock()
            app.tts = MagicMock()
            app.state_mgr = MagicMock()
            app.go_to_sleep = MagicMock()
            app._load_config = MagicMock(return_value={})

            app.on_text_recognized("lock the pc")
            app.executor.execute.assert_called_once()
            app.go_to_sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
