import threading
from typing import Optional

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

class TTSEngine:
    """Provides non-blocking, offline speech synthesis using Windows SAPI5."""

    def __init__(self, enabled: bool = True, rate: int = 185, volume: float = 1.0):
        self.enabled = enabled and TTS_AVAILABLE
        self.rate = rate
        self.volume = volume
        self._lock = threading.Lock()

    def speak(self, text: str):
        if not self.enabled or not text.strip():
            return

        def _worker():
            with self._lock:
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.rate)
                    engine.setProperty("volume", self.volume)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    print(f"TTS error: {e}")

        # Run non-blocking in background thread
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
