import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from typing import Callable, List, Optional, Tuple

from voice.base_recognizer import BaseVoiceRecognizer
from voice.vosk_recognizer import VoskVoiceRecognizer

SUPPORTED_ENGINES = ("vosk", "faster_whisper", "windows_native", "groq_whisper")

VOSK_MODEL_DIR = "vosk-model-small-en-us-0.15"
VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
FASTER_WHISPER_DIR = "faster-whisper"


def get_models_cache_dir(base_dir: str) -> str:
    """Returns a user-writable model cache directory (%LOCALAPPDATA%/PHOENIX/models on Windows)."""
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        cache_dir = os.path.join(local_app_data, "PHOENIX", "models")
    else:
        cache_dir = os.path.join(base_dir, "models")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def resolve_vosk_model_path(base_dir: str) -> Optional[str]:
    """Finds Vosk model in user cache or bundled project models/ folder."""
    cache_path = os.path.join(get_models_cache_dir(base_dir), VOSK_MODEL_DIR)
    if os.path.exists(cache_path):
        return cache_path
    bundled_path = os.path.join(base_dir, "models", VOSK_MODEL_DIR)
    if os.path.exists(bundled_path):
        return bundled_path
    return None


def _delete_cached_models(cache_dir: str, keep_prefix: str = ""):
    """Removes previously cached local models from %LOCALAPPDATA%/PHOENIX/models to enforce single-model cache."""
    if not os.path.exists(cache_dir):
        return
    for entry in os.listdir(cache_dir):
        if keep_prefix and entry.startswith(keep_prefix):
            continue
        target = os.path.join(cache_dir, entry)
        try:
            if os.path.isdir(target):
                shutil.rmtree(target, ignore_errors=True)
            elif os.path.isfile(target):
                os.remove(target)
        except Exception as e:
            print(f"[VOICE-MGR] Cleanup warning for {entry}: {e}")


def _ensure_vosk_installed(cache_dir: str, base_dir: str) -> str:
    existing = resolve_vosk_model_path(base_dir)
    if existing:
        return existing

    zip_path = os.path.join(cache_dir, f"{VOSK_MODEL_DIR}.zip")
    target_path = os.path.join(cache_dir, VOSK_MODEL_DIR)
    urllib.request.urlretrieve(VOSK_MODEL_URL, zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(cache_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    return target_path


def _ensure_faster_whisper_installed(cache_dir: str) -> str:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "faster-whisper", "--quiet"])

    from faster_whisper import WhisperModel

    fw_dir = os.path.join(cache_dir, FASTER_WHISPER_DIR)
    os.makedirs(fw_dir, exist_ok=True)
    # Trigger download/verification of tiny.en INT8 model into cache_dir
    WhisperModel("tiny.en", device="cpu", compute_type="int8", cpu_threads=2, download_root=fw_dir)
    return fw_dir


def switch_and_sync_engine(
    target_engine: str,
    base_dir: str,
    groq_api_key: str = "",
) -> Tuple[bool, str]:
    """
    Installs/verifies the chosen voice engine, deletes older cached local models,
    and updates config/settings.json.
    """
    engine = (target_engine or "vosk").strip().lower()
    if engine not in SUPPORTED_ENGINES:
        return False, f"Unsupported voice engine '{engine}'. Choose from: {', '.join(SUPPORTED_ENGINES)}."

    if engine == "groq_whisper" and not (groq_api_key or "").strip():
        return False, "Groq Cloud Whisper requires a Groq API key."

    cache_dir = get_models_cache_dir(base_dir)

    try:
        if engine == "vosk":
            _ensure_vosk_installed(cache_dir, base_dir)
            _delete_cached_models(cache_dir, keep_prefix="vosk-model")
        elif engine == "faster_whisper":
            _ensure_faster_whisper_installed(cache_dir)
            _delete_cached_models(cache_dir, keep_prefix=FASTER_WHISPER_DIR)
        elif engine in ("windows_native", "groq_whisper"):
            # Zero local model needed — clean up any cached local models
            _delete_cached_models(cache_dir, keep_prefix="")
    except Exception as e:
        return False, f"Failed to prepare {engine}: {e}"

    settings_path = os.path.join(base_dir, "config", "settings.json")
    try:
        cfg = {}
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        cfg.setdefault("voice", {})["engine"] = engine
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        return False, f"Model prepared, but failed to save settings: {e}"

    return True, f"Voice engine switched to {engine}."


class VoiceEngineManager:
    """Factory that loads the configured speech recognizer with safe fallback."""

    @staticmethod
    def create_recognizer(
        config: dict,
        base_dir: str,
        grammar_phrases: Optional[List[str]] = None,
        on_text_recognized: Optional[Callable[[str], None]] = None,
        on_partial: Optional[Callable[[str], None]] = None,
        tts_is_speaking: Optional[Callable[[], bool]] = None,
    ) -> BaseVoiceRecognizer:
        voice_cfg = config.get("voice", {})
        ai_cfg = config.get("ai", {})
        engine = voice_cfg.get("engine", "vosk").strip().lower()
        sample_rate = voice_cfg.get("sample_rate", 16000)
        silence_timeout = voice_cfg.get("silence_timeout_seconds", 1.2)
        energy_threshold = voice_cfg.get("energy_threshold", 250.0)
        cache_dir = get_models_cache_dir(base_dir)

        if engine == "windows_native":
            from voice.adapters.windows_native import WindowsNativeRecognizer

            return WindowsNativeRecognizer(
                grammar_phrases=grammar_phrases,
                on_text_recognized=on_text_recognized,
                on_partial=on_partial,
                tts_is_speaking=tts_is_speaking,
            )

        if engine == "groq_whisper":
            api_key = ai_cfg.get("groq_api_key", "") or os.environ.get("GROQ_API_KEY", "")
            if api_key.strip():
                from voice.adapters.groq_whisper_adapter import GroqWhisperRecognizer

                return GroqWhisperRecognizer(
                    api_key=api_key,
                    sample_rate=sample_rate,
                    silence_timeout=silence_timeout,
                    energy_threshold=energy_threshold,
                    grammar_phrases=grammar_phrases,
                    on_text_recognized=on_text_recognized,
                    on_partial=on_partial,
                    tts_is_speaking=tts_is_speaking,
                )
            print("[VOICE-MGR] Groq API key missing for groq_whisper; falling back to Vosk/Windows Native.")

        if engine == "faster_whisper":
            try:
                from voice.adapters.faster_whisper_adapter import FasterWhisperRecognizer

                fw_dir = os.path.join(cache_dir, FASTER_WHISPER_DIR)
                return FasterWhisperRecognizer(
                    model_size="tiny.en",
                    download_root=fw_dir,
                    sample_rate=sample_rate,
                    silence_timeout=silence_timeout,
                    energy_threshold=energy_threshold,
                    grammar_phrases=grammar_phrases,
                    on_text_recognized=on_text_recognized,
                    on_partial=on_partial,
                    tts_is_speaking=tts_is_speaking,
                )
            except Exception as e:
                print(f"[VOICE-MGR] Faster-Whisper load failed ({e}); falling back to Vosk.")

        # Default: Vosk
        model_path = resolve_vosk_model_path(base_dir)
        if model_path:
            return VoskVoiceRecognizer(
                model_path=model_path,
                sample_rate=sample_rate,
                silence_timeout=silence_timeout,
                energy_threshold=energy_threshold,
                grammar_phrases=grammar_phrases,
                on_text_recognized=on_text_recognized,
                on_partial=on_partial,
                tts_is_speaking=tts_is_speaking,
            )

        # Zero-download emergency fallback if Vosk model isn't present
        from voice.adapters.windows_native import WindowsNativeRecognizer

        print("[VOICE-MGR] Vosk model not found; using Windows Native Speech fallback.")
        return WindowsNativeRecognizer(
            grammar_phrases=grammar_phrases,
            on_text_recognized=on_text_recognized,
            on_partial=on_partial,
            tts_is_speaking=tts_is_speaking,
        )
