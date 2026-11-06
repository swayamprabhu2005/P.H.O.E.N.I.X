import json
import os
import queue
import threading
import time
from typing import Callable, Optional, List
import numpy as np
import sounddevice as sd
import vosk
from vosk import Model, KaldiRecognizer

# Completely silence Kaldi C++ engine debug logs
vosk.SetLogLevel(-1)

class VoskVoiceRecognizer:
    """Manages microphone audio capture and offline streaming speech recognition with Vosk."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        sample_rate: int = 16000,
        silence_timeout: float = 1.2,
        energy_threshold: float = 250.0,
        grammar_phrases: Optional[List[str]] = None,
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
        self.energy_threshold = energy_threshold
        self.dynamic_threshold = energy_threshold
        self.ambient_noise_level = max(50.0, energy_threshold * 0.4)
        self._calibrated = False
        self.on_text_recognized = on_text_recognized
        self.on_partial = on_partial
        self.grammar_phrases = grammar_phrases or []

        self.model = Model(self.model_path)
        self._init_recognizer(self.grammar_phrases)
        self._init_audio_filter()

        self._audio_queue = queue.Queue()
        self._is_listening = False
        self._worker_thread = None
        self._stream = None
        self._last_speech_time = 0.0
        self._has_detected_speech = False

    def _init_recognizer(self, grammar_phrases: List[str]):
        """Initializes or resets KaldiRecognizer with constrained grammar and unknown token."""
        if grammar_phrases:
            clean_list = sorted(list(set([p.lower().strip() for p in grammar_phrases if p.strip()])))
            if "[unk]" not in clean_list:
                clean_list.append("[unk]")
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate, json.dumps(clean_list))
        else:
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)

    def _init_audio_filter(self):
        """Initializes 2nd-order Butterworth bandpass filter (80 Hz - 7500 Hz)."""
        try:
            from scipy.signal import butter, sosfilt_zi
            self._filter_sos = butter(2, [80, 7500], btype="bandpass", fs=self.sample_rate, output="sos")
            self._filter_zi = sosfilt_zi(self._filter_sos) * 0.0
            self._has_filter = True
        except Exception:
            self._has_filter = False

    def _filter_audio(self, samples: np.ndarray) -> np.ndarray:
        """Removes low-frequency fan/desk vibrations (<80 Hz) and high-frequency noise (>7500 Hz)."""
        if not getattr(self, "_has_filter", False):
            return samples
        try:
            from scipy.signal import sosfilt
            filtered, self._filter_zi = sosfilt(self._filter_sos, samples.astype(np.float32), zi=self._filter_zi)
            return np.clip(filtered, -32768, 32767).astype(np.int16)
        except Exception:
            return samples

    def set_grammar(self, phrases: List[str]):
        """Updates the grammar dictionary dynamically."""
        self.grammar_phrases = phrases
        self._init_recognizer(self.grammar_phrases)

    def calibrate_ambient_noise(self, duration: float = 0.5):
        """Samples ambient room noise to establish an optimal adaptive noise gate threshold."""
        samples = []
        try:
            def _calib_cb(indata, frames, time_info, status):
                s = np.frombuffer(bytes(indata), dtype=np.int16)
                if len(s) > 0:
                    rms = float(np.sqrt(np.mean(s.astype(float)**2)))
                    samples.append(rms)

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=1024,
                dtype="int16",
                channels=1,
                callback=_calib_cb
            ):
                time.sleep(duration)

            if samples:
                avg_noise = float(np.mean(samples))
                std_noise = float(np.std(samples))
                calculated = max(100.0, avg_noise + 2.5 * std_noise + 75.0)
                self.ambient_noise_level = avg_noise
                self.dynamic_threshold = calculated
                self.energy_threshold = calculated
                self._calibrated = True
                print(f"[VOSK] Ambient Noise Calibrated: Floor={avg_noise:.1f} RMS -> Dynamic Gate={calculated:.1f} RMS", flush=True)
        except Exception as e:
            print(f"[VOSK] Ambient calibration note: {e}", flush=True)

    def _audio_callback(self, indata, frames, time_info, status):
        if not self._is_listening:
            return

        audio_bytes = bytes(indata)

        # 1. Bandpass filter: Cut rumble (<80 Hz) and squeal (>7500 Hz)
        try:
            raw_samples = np.frombuffer(audio_bytes, dtype=np.int16)
            filtered_samples = self._filter_audio(raw_samples)
            filtered_bytes = filtered_samples.tobytes()
            rms = float(np.sqrt(np.mean(filtered_samples.astype(float)**2)))
        except Exception:
            filtered_bytes = audio_bytes
            rms = self.dynamic_threshold + 10.0

        # 2. Slow adaptive tracking when room is quiet and no speech is in progress
        if not self._has_detected_speech and rms < self.dynamic_threshold * 0.75:
            self.ambient_noise_level = 0.96 * self.ambient_noise_level + 0.04 * rms
            self.dynamic_threshold = max(100.0, self.ambient_noise_level + 90.0)
            self.energy_threshold = self.dynamic_threshold

        # 3. Dynamic RMS Noise Gate
        if rms >= self.dynamic_threshold:
            self._has_detected_speech = True
            self._last_speech_time = time.time()
            self._audio_queue.put(filtered_bytes)
        elif self._has_detected_speech:
            # Trailing audio after speech to allow sentence closure
            if time.time() - self._last_speech_time <= self.silence_timeout:
                self._audio_queue.put(filtered_bytes)

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
                    if text and text != "[unk]" and self.on_text_recognized:
                        self.on_text_recognized(text)
                    self.recognizer.Reset()
                    self._has_detected_speech = False
                continue

            if self.recognizer.AcceptWaveform(data):
                res = json.loads(self.recognizer.Result())
                text = res.get("text", "").strip()
                if text and text != "[unk]":
                    self._has_detected_speech = False
                    if self.on_text_recognized:
                        self.on_text_recognized(text)
            else:
                partial = json.loads(self.recognizer.PartialResult())
                partial_text = partial.get("partial", "").strip()
                if partial_text and partial_text != "[unk]":
                    self._has_detected_speech = True
                    self._last_speech_time = time.time()
                    if self.on_partial:
                        self.on_partial(partial_text)
