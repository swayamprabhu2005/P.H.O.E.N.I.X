import threading
import time
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
        self._speaking = False
        self._speaking_until = 0.0

    @property
    def is_speaking(self) -> bool:
        """Returns True while TTS is actively speaking or within post-speech echo tail guard."""
        return self._speaking or (time.time() < self._speaking_until)

    def speak(self, text: str):
        if not self.enabled or not text.strip():
            return

        # Mark speaking immediately so mic gate engages before audio thread starts
        self._speaking = True

        def _worker():
            with self._lock:
                self._speaking = True
                try:
                    engine = pyttsx3.init()
                    engine.setProperty("rate", self.rate)
                    engine.setProperty("volume", self.volume)
                    engine.say(text)
                    engine.runAndWait()
                    engine.stop()
                except Exception as e:
                    print(f"TTS error: {e}")
                finally:
                    self._speaking = False
                    # 300ms tail guard to let speaker/room echo decay before re-opening mic
                    self._speaking_until = time.time() + 0.30

        # Run non-blocking in background thread
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
