import io
import json
import queue
import threading
import time
import urllib.request
import uuid
import wave
from typing import Callable, List, Optional
import numpy as np
import sounddevice as sd

from voice.audio_pipeline import AudioPipeline
from voice.base_recognizer import BaseVoiceRecognizer


class GroqWhisperRecognizer(BaseVoiceRecognizer):
    """
    Zero-local-model cloud speech recognizer using Groq's whisper-large-v3 endpoint.
    """

    engine_name = "groq_whisper"

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-large-v3",
        sample_rate: int = 16000,
        silence_timeout: float = 1.0,
        energy_threshold: float = 250.0,
        grammar_phrases: Optional[List[str]] = None,
        on_text_recognized: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
        tts_is_speaking: Optional[Callable[[], bool]] = None,
    ):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.on_text_recognized = on_text_recognized
        self.on_partial = on_partial
        self.grammar_phrases = grammar_phrases or []
        self.endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

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
            print(f"[GROQ-WHISPER] Calibration note: {e}")

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
            print(f"[GROQ-WHISPER] Mic error: {e}")
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

    def _transcribe_wav(self, pcm_bytes: bytes) -> str:
        if not self.api_key:
            return ""

        wav_io = io.BytesIO()
        with wave.open(wav_io, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_bytes)

        boundary = f"----PhoenixBoundary{uuid.uuid4().hex}"
        body = bytearray()
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="file"; filename="speech.wav"\r\nContent-Type: audio/wav\r\n\r\n')
        body.extend(wav_io.getvalue())
        body.extend(f"\r\n--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="model"\r\n\r\n')
        body.extend(self.model.encode())
        body.extend(f"\r\n--{boundary}\r\n".encode())
        body.extend(b'Content-Disposition: form-data; name="language"\r\n\r\nen')
        body.extend(f"\r\n--{boundary}--\r\n".encode())

        req = urllib.request.Request(
            self.endpoint,
            data=bytes(body),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "PHOENIX-Agent/1.1",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("text", "").strip().lower()
        except Exception as e:
            print(f"[GROQ-WHISPER] Transcription failed: {e}")
            return ""

    def _process_stream(self):
        buffer = bytearray()
        while self._is_listening:
            try:
                chunk = self._audio_queue.get(timeout=0.1)
                buffer.extend(chunk)
            except queue.Empty:
                if buffer and self._has_detected_speech and (time.time() - self._last_speech_time > self.silence_timeout):
                    pcm = bytes(buffer)
                    buffer.clear()
                    self._has_detected_speech = False
                    if len(pcm) >= int(self.sample_rate * 2 * 0.25):
                        text = self._transcribe_wav(pcm)
                        if text and self.on_text_recognized:
                            self.on_text_recognized(text)
