import json
import os
import queue
import threading
import time
from typing import Callable, Optional
import sounddevice as sd
from vosk import Model, KaldiRecognizer

class VoskVoiceRecognizer:
    """Manages microphone audio capture and offline streaming speech recognition with Vosk."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
        silence_timeout: float = 1.2,
        on_text_recognized: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if model_path is None:
            model_path = os.path.join(base_dir, "models", "vosk-model-small-en-us-0.15")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at {model_path}")

        self.model_path = model_path
        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.on_text_recognized = on_text_recognized
        self.on_partial = on_partial

        self.model = Model(self.model_path)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

        self._audio_queue = queue.Queue()
        self._is_listening = False
        self._worker_thread = None
        self._stream = None
        self._last_speech_time = 0.0
        self._has_detected_speech = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            print(f"Audio status: {status}", flush=True)
        if self._is_listening:
            self._audio_queue.put(bytes(indata))

    def start_listening(self):
        """Activates microphone and starts processing audio stream."""
        if self._is_listening:
            return

        self._is_listening = True
        self._has_detected_speech = False
        self._last_speech_time = time.time()
        self.recognizer.Reset()

        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break

        try:
            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype="int16",
                channels=1,
                callback=self._audio_callback
            )
            self._stream.start()
        except Exception as e:
            print(f"Failed to open microphone stream: {e}")
            self._is_listening = False
            return

        self._worker_thread = threading.Thread(target=self._process_stream, daemon=True)
        self._worker_thread.start()

    def stop_listening(self):
        """Stops audio stream and releases microphone hardware."""
        self._is_listening = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _process_stream(self):
        while self._is_listening:
            try:
                data = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                # Check for silence timeout if we already heard speech
                if self._has_detected_speech and (time.time() - self._last_speech_time > self.silence_timeout):
                    final_res = json.loads(self.recognizer.FinalResult())
                    text = final_res.get("text", "").strip()
                    if text and self.on_text_recognized:
                        self.on_text_recognized(text)
                    self.recognizer.Reset()
                    self._has_detected_speech = False
                continue

            if self.recognizer.AcceptWaveform(data):
                res = json.loads(self.recognizer.Result())
                text = res.get("text", "").strip()
                if text:
                    self._has_detected_speech = False
                    if self.on_text_recognized:
                        self.on_text_recognized(text)
            else:
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text:
                    self._has_detected_speech = True
                    self._last_speech_time = time.time()
                    if self.on_partial:
                        self.on_partial(partial_text)
