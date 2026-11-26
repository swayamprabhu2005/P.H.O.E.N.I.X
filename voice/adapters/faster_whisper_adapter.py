import queue
import threading
import time
from typing import Callable, List, Optional
import numpy as np
import sounddevice as sd

from voice.audio_pipeline import AudioPipeline
from voice.base_recognizer import BaseVoiceRecognizer


class FasterWhisperRecognizer(BaseVoiceRecognizer):
    """
    Offline Faster-Whisper (tiny.en INT8 CPU) recognizer using shared AudioPipeline VAD.
    """

    engine_name = "faster_whisper"

    def __init__(
        self,
        model_size: str = "tiny.en",
        download_root: Optional[str] = None,
        sample_rate: int = 16000,
        silence_timeout: float = 1.0,
        energy_threshold: float = 250.0,
        grammar_phrases: Optional[List[str]] = None,
        on_text_recognized: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
        tts_is_speaking: Optional[Callable[[], bool]] = None,
    ):
        from faster_whisper import WhisperModel

        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.on_text_recognized = on_text_recognized
        self.on_partial = on_partial
        self.grammar_phrases = grammar_phrases or []

        self.model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
            cpu_threads=2,
            download_root=download_root,
        )
        self.pipeline = AudioPipeline(
            sample_rate=sample_rate,
            energy_threshold=energy_threshold,
            tts_is_speaking=tts_is_speaking,
        )

        self._audio_queue: queue.Queue = queue.Queue()
        self._is_listening = False
        self._stream = None
        self._worker_thread = None
        self._has_detected_speech = False
        self._last_speech_time = 0.0

    def set_grammar(self, phrases: List[str]):
        self.grammar_phrases = phrases or []

    def calibrate_ambient_noise(self, duration: float = 0.5):
        frames = []
        try:
            def _calib_cb(indata, frames_count, time_info, status):
                s = np.frombuffer(bytes(indata), dtype=np.int16)
                if len(s) > 0:
                    frames.append(s.copy())

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=1000,
                dtype="int16",
                channels=1,
                callback=_calib_cb,
            ):
                time.sleep(duration)
            if frames:
                self.pipeline.calibrate_from_frames(frames)
        except Exception as e:
            print(f"[FASTER-WHISPER] Calibration note: {e}")

    def _audio_callback(self, indata, frames, time_info, status):
        if not self._is_listening:
            return
        cleaned, is_speech, _ = self.pipeline.process_frame(
            bytes(indata), speech_in_progress=self._has_detected_speech
        )
        if cleaned is None:
            self._has_detected_speech = False
            return
        if is_speech:
            self._has_detected_speech = True
            self._last_speech_time = time.time()
            self._audio_queue.put(cleaned)
        elif self._has_detected_speech and (time.time() - self._last_speech_time <= self.silence_timeout):
            self._audio_queue.put(cleaned)

    def start_listening(self):
        if self._is_listening:
            return
        self._is_listening = True
        self._has_detected_speech = False
        self._last_speech_time = time.time()

        try:
            self._stream = sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=4000,
                dtype="int16",
                channels=1,
                callback=self._audio_callback,
            )
            self._stream.start()
            self._worker_thread = threading.Thread(target=self._process_stream, daemon=True)
            self._worker_thread.start()
        except Exception as e:
            print(f"[FASTER-WHISPER] Mic error: {e}")
            self._is_listening = False

    def stop_listening(self):
        self._is_listening = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _process_stream(self):
        buffer = bytearray()
        while self._is_listening:
            try:
                chunk = self._audio_queue.get(timeout=0.1)
                buffer.extend(chunk)
            except queue.Empty:
                if buffer and self._has_detected_speech and (time.time() - self._last_speech_time > self.silence_timeout):
                    audio_np = np.frombuffer(bytes(buffer), dtype=np.int16).astype(np.float32) / 32768.0
                    buffer.clear()
                    self._has_detected_speech = False
                    if len(audio_np) >= int(self.sample_rate * 0.25):
                        segments, _ = self.model.transcribe(audio_np, language="en", beam_size=1, vad_filter=False)
                        text = " ".join(seg.text.strip() for seg in segments).strip().lower()
                        if text and self.on_text_recognized:
                            self.on_text_recognized(text)
