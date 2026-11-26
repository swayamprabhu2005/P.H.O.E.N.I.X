from abc import ABC, abstractmethod
from typing import List


class BaseVoiceRecognizer(ABC):
    """Unified interface for pluggable P.H.O.E.N.I.X. speech recognition engines."""

    engine_name: str = "base"

    @abstractmethod
    def start_listening(self):
        """Activates microphone capture and starts recognition."""

    @abstractmethod
    def stop_listening(self):
        """Stops recognition and releases microphone hardware."""

    @abstractmethod
    def set_grammar(self, phrases: List[str]):
        """Updates active command phrase hints/grammar."""

    @abstractmethod
    def calibrate_ambient_noise(self, duration: float = 0.5):
        """Samples ambient noise floor for adaptive gating."""
