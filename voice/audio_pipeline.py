import numpy as np
from typing import Callable, Optional, Tuple


class AudioPipeline:
    """
    Lightweight, CPU-only multi-stage speech conditioning pipeline for 4GB RAM systems.
    Stages:
      1. Half-duplex TTS echo gate (drops frames while assistant speaks)
      2. DC-offset removal + 2nd-order Butterworth bandpass (100 Hz - 7000 Hz)
      3. Stationary spectral noise subtraction (FFT profile calibrated from room/system noise)
      4. Vocal-band Energy + Speech-ratio VAD
      5. Gentle consonant pre-emphasis + soft peak normalization
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        energy_threshold: float = 250.0,
        tts_is_speaking: Optional[Callable[[], bool]] = None,
        noise_oversubtraction: float = 1.6,
        spectral_floor: float = 0.08,
    ):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.dynamic_threshold = energy_threshold
        self.ambient_noise_level = max(50.0, energy_threshold * 0.4)
        self.tts_is_speaking = tts_is_speaking
        self.noise_oversubtraction = noise_oversubtraction
        self.spectral_floor = spectral_floor

        self._noise_profile: Optional[np.ndarray] = None
        self._noise_nfft: int = 0
        self._prev_sample: float = 0.0
        self._init_bandpass()

    def _init_bandpass(self):
        try:
            from scipy.signal import butter, sosfilt_zi

            nyquist = self.sample_rate * 0.5
            high = min(7000.0, nyquist - 200.0)
            self._filter_sos = butter(2, [100.0, high], btype="bandpass", fs=self.sample_rate, output="sos")
            self._filter_zi = sosfilt_zi(self._filter_sos) * 0.0
            self._has_filter = True
        except Exception:
            self._has_filter = False

    def calibrate_from_frames(self, frames: list):
        """Builds both scalar RMS floor and per-frequency spectral noise profile."""
        if not frames:
            return

        rms_values = []
        spectra = []
        target_nfft = len(frames[0])

        for frame in frames:
            arr = frame.astype(np.float32)
            if len(arr) == 0:
                continue
            arr = arr - np.mean(arr)
            rms = float(np.sqrt(np.mean(arr ** 2)))
            rms_values.append(rms)
            if len(arr) == target_nfft:
                win = np.hanning(len(arr))
                spectra.append(np.abs(np.fft.rfft(arr * win)))

        if rms_values:
            avg_noise = float(np.mean(rms_values))
            std_noise = float(np.std(rms_values))
            self.ambient_noise_level = avg_noise
            self.dynamic_threshold = max(110.0, avg_noise + 2.5 * std_noise + 80.0)
            self.energy_threshold = self.dynamic_threshold

        if spectra:
            self._noise_profile = np.mean(spectra, axis=0).astype(np.float32)
            self._noise_nfft = target_nfft

    def _apply_bandpass(self, samples: np.ndarray) -> np.ndarray:
        if not self._has_filter:
            return samples
        try:
            from scipy.signal import sosfilt

            filtered, self._filter_zi = sosfilt(self._filter_sos, samples, zi=self._filter_zi)
            return filtered.astype(np.float32)
        except Exception:
            return samples

    def _spectral_denoise(self, samples: np.ndarray) -> np.ndarray:
        """Subtracts stationary background/fan/system hum in frequency domain."""
        if self._noise_profile is None or len(samples) != self._noise_nfft:
            return samples

        win = np.hanning(len(samples)).astype(np.float32)
        spectrum = np.fft.rfft(samples * win)
        mag = np.abs(spectrum)
        phase = np.angle(spectrum)

        # Soft spectral subtraction with floor to avoid musical noise artifacts
        cleaned_mag = np.maximum(
            mag - self.noise_oversubtraction * self._noise_profile,
            self.spectral_floor * mag,
        )
        reconstructed = np.fft.irfft(cleaned_mag * np.exp(1j * phase), n=len(samples))
        return reconstructed.astype(np.float32)

    def _vocal_band_ratio(self, samples: np.ndarray) -> float:
        """Returns fraction of energy in human speech band (300 Hz - 3400 Hz)."""
        if len(samples) < 64:
            return 1.0
        mag2 = np.abs(np.fft.rfft(samples)) ** 2
        total = float(np.sum(mag2)) + 1e-9
        freqs = np.fft.rfftfreq(len(samples), d=1.0 / self.sample_rate)
        vocal_mask = (freqs >= 300.0) & (freqs <= 3400.0)
        vocal_energy = float(np.sum(mag2[vocal_mask]))
        return vocal_energy / total

    def _pre_emphasis(self, samples: np.ndarray, coeff: float = 0.85) -> np.ndarray:
        """Sharpens consonant formants (s, t, k, p) for small acoustic models."""
        if len(samples) == 0:
            return samples
        emphasized = np.empty_like(samples)
        emphasized[0] = samples[0] - coeff * self._prev_sample
        emphasized[1:] = samples[1:] - coeff * samples[:-1]
        self._prev_sample = float(samples[-1])
        return emphasized

    def process_frame(self, raw_bytes: bytes, speech_in_progress: bool = False) -> Tuple[Optional[bytes], bool, float]:
        """
        Conditions a 16-bit PCM frame.
        Returns: (cleaned_pcm_bytes or None if gated/TTS, is_speech_detected, rms_level)
        """
        if self.tts_is_speaking and self.tts_is_speaking():
            return None, False, 0.0

        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)
        if len(samples) == 0:
            return None, False, 0.0

        # 1. DC-offset removal + speech bandpass
        samples = samples - np.mean(samples)
        samples = self._apply_bandpass(samples)

        # 2. Spectral noise subtraction (when frame size matches calibrated profile)
        if self._noise_profile is not None and len(samples) == self._noise_nfft:
            samples = self._spectral_denoise(samples)
        elif self._noise_profile is not None and len(samples) > self._noise_nfft and len(samples) % self._noise_nfft == 0:
            chunks = np.split(samples, len(samples) // self._noise_nfft)
            samples = np.concatenate([self._spectral_denoise(c) for c in chunks])

        rms = float(np.sqrt(np.mean(samples ** 2)))

        # 3. Adaptive quiet-room floor tracking
        if not speech_in_progress and rms < self.dynamic_threshold * 0.75:
            self.ambient_noise_level = 0.96 * self.ambient_noise_level + 0.04 * rms
            self.dynamic_threshold = max(110.0, self.ambient_noise_level + 90.0)
            self.energy_threshold = self.dynamic_threshold

        # 4. Energy + Vocal Band VAD
        is_speech = False
        if rms >= self.dynamic_threshold:
            vocal_ratio = self._vocal_band_ratio(samples)
            if vocal_ratio >= 0.35 or speech_in_progress:
                is_speech = True

        # 5. Pre-emphasis + soft peak normalization (prevent clipping, boost quiet speech)
        conditioned = self._pre_emphasis(samples)
        peak = float(np.max(np.abs(conditioned)))
        if 500.0 < peak < 12000.0 and is_speech:
            gain = min(2.2, 14000.0 / peak)
            conditioned = conditioned * gain

        pcm_out = np.clip(conditioned, -32768.0, 32767.0).astype(np.int16).tobytes()
        return pcm_out, is_speech, rms
