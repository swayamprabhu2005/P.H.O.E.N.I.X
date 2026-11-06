import os
from typing import Callable, Optional
import webview

class WindowApi:
    """Methods exposed directly to frontend JavaScript via window.pywebview.api."""

    def __init__(
        self,
        on_wake: Callable[[], None],
        on_sleep: Callable[[], None],
        on_hide: Callable[[], None],
        on_change_name: Optional[Callable[[str], None]] = None
    ):
        self.on_wake = on_wake
        self.on_sleep = on_sleep
        self.on_hide = on_hide
        self.on_change_name = on_change_name

    def wake_up(self):
        if self.on_wake:
            self.on_wake()

    def go_to_sleep(self):
        if self.on_sleep:
            self.on_sleep()

    def hide_window(self):
        if self.on_hide:
            self.on_hide()

    def change_name(self, new_name: str):
        if self.on_change_name:
            self.on_change_name(new_name)

class DesktopWindowManager:
    """Manages the pywebview transparent floating desktop HUD."""

    def __init__(
        self,
        on_wake: Optional[Callable[[], None]] = None,
        on_sleep: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
        on_change_name: Optional[Callable[[str], None]] = None,
        width: int = 380,
        height: int = 430
    ):
        self.on_wake = on_wake
        self.on_sleep = on_sleep
        self.on_hide = on_hide
        self.on_change_name = on_change_name
        self.width = width
        self.height = height

        self.api = WindowApi(self._handle_wake, self._handle_sleep, self._handle_hide, self._handle_change_name)
        self.window = None

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(base_dir, "visual", "index.html")

    def _handle_wake(self):
        if self.on_wake:
            self.on_wake()

    def _handle_sleep(self):
        if self.on_sleep:
            self.on_sleep()

    def _handle_hide(self):
        if self.on_hide:
            self.on_hide()

    def _handle_change_name(self, new_name: str):
        if self.on_change_name:
            self.on_change_name(new_name)

    def create_window(self):
        """Creates the transparent frameless pywebview window."""
        self.window = webview.create_window(
            title="P.H.O.E.N.I.X.",
            url=self.html_path,
            js_api=self.api,
            width=self.width,
            height=self.height,
            frameless=True,
            easy_drag=True,
            on_top=True,
            transparent=True,
            background_color="#000000"
        )
        return self.window

    def update_ui_state(self, state: str, message: str = "", active_path: str = ""):
        """Invokes window.updateState in frontend JavaScript."""
        if self.window:
            safe_msg = message.replace("'", "\\'").replace('"', '\\"').replace("\n", " ")
            safe_path = active_path.replace("\\", "\\\\")
            js = f"if (window.updateState) window.updateState('{state}', '{safe_msg}', '{safe_path}');"
            try:
                self.window.evaluate_js(js)
            except Exception as e:
                print(f"Error updating UI state: {e}")

    def show_feedback(self, cmd_text: str, result_text: str, is_success: bool = True):
        """Invokes window.showFeedback in frontend JavaScript."""
        if self.window:
            safe_cmd = cmd_text.replace("'", "\\'").replace('"', '\\"')
            safe_res = result_text.replace("'", "\\'").replace('"', '\\"')
            bool_str = "true" if is_success else "false"
            js = f"if (window.showFeedback) window.showFeedback('{safe_cmd}', '{safe_res}', {bool_str});"
            try:
                self.window.evaluate_js(js)
            except Exception as e:
                print(f"Error showing feedback: {e}")

    def show(self):
        if self.window:
            try:
                self.window.show()
            except Exception:
                pass

    def hide(self):
        if self.window:
            try:
                self.window.hide()
            except Exception:
                pass

    def destroy(self):
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
