from enum import Enum

class AppState(Enum):
    STANDBY = "standby"
    LISTENING = "listening"
    PROCESSING = "processing"
    EXECUTING = "executing"

class StateManager:
    """Tracks and notifies state transitions across P.H.O.E.N.I.X."""

    def __init__(self, initial_state: AppState = AppState.STANDBY):
        self._current_state = initial_state
        self._listeners = []

    @property
    def current_state(self) -> AppState:
        return self._current_state

    def add_listener(self, callback):
        self._listeners.append(callback)

    def transition_to(self, new_state: AppState):
        if self._current_state != new_state:
            old_state = self._current_state
            self._current_state = new_state
            for cb in self._listeners:
                try:
                    cb(new_state, old_state)
                except Exception as e:
                    print(f"Error in state listener: {e}")
