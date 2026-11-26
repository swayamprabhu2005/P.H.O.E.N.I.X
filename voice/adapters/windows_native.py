import subprocess
import threading
from typing import Callable, List, Optional
from voice.base_recognizer import BaseVoiceRecognizer


class WindowsNativeRecognizer(BaseVoiceRecognizer):
    """
    Zero-download speech recognizer using Windows built-in System.Speech (SAPI).
    Consumes 0 MB disk download and minimal RAM on Windows 10/11.
    """

    engine_name = "windows_native"

    def __init__(
        self,
        grammar_phrases: Optional[List[str]] = None,
        on_text_recognized: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
        tts_is_speaking: Optional[Callable[[], bool]] = None,
    ):
        self.grammar_phrases = grammar_phrases or []
        self.on_text_recognized = on_text_recognized
        self.on_partial = on_partial
        self.tts_is_speaking = tts_is_speaking
        self._is_listening = False
        self._proc: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None

    def set_grammar(self, phrases: List[str]):
        self.grammar_phrases = phrases or []

    def calibrate_ambient_noise(self, duration: float = 0.5):
        # Handled natively by Windows Speech engine
        pass

    def start_listening(self):
        if self._is_listening:
            return
        self._is_listening = True

        ps_script = (
            "Add-Type -AssemblyName System.Speech; "
            "$rec = New-Object System.Speech.Recognition.SpeechRecognitionEngine; "
            "$rec.SetInputToDefaultAudioDevice(); "
            "$rec.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar)); "
            "while ($true) { "
            "$res = $rec.Recognize([TimeSpan]::FromSeconds(1.2)); "
            "if ($res -and $res.Text) { [Console]::Out.WriteLine($res.Text); [Console]::Out.Flush() } "
            "}"
        )

        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self._proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                creationflags=creation_flags,
            )
            self._thread = threading.Thread(target=self._read_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            print(f"[WIN-SAPI] Failed to start native speech recognizer: {e}")
            self._is_listening = False

    def _read_loop(self):
        while self._is_listening and self._proc and self._proc.stdout:
            line = self._proc.stdout.readline()
            if not line:
                break
            text = line.strip()
            if not text:
                continue
            if self.tts_is_speaking and self.tts_is_speaking():
                continue
            if self.on_text_recognized:
                self.on_text_recognized(text.lower())

    def stop_listening(self):
        self._is_listening = False
        if self._proc:
            try:
                self._proc.terminate()
            except Exception:
                pass
            self._proc = None
