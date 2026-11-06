import ctypes
import json
import os
import threading
import time
from typing import Callable, Optional, Dict, Any
import webview

class WindowApi:
    """Methods exposed directly to frontend JavaScript via window.pywebview.api."""

    def __init__(
        self,
        on_wake: Callable[[], None],
        on_sleep: Callable[[], None],
        on_hide: Callable[[], None],
        on_change_name: Optional[Callable[[str], None]] = None,
        on_confirm_action: Optional[Callable[[bool, str, str, Dict[str, Any]], None]] = None,
        on_save_groq_key: Optional[Callable[[str], None]] = None
    ):
        self.on_wake = on_wake
        self.on_sleep = on_sleep
        self.on_hide = on_hide
        self.on_change_name = on_change_name
        self.on_confirm_action = on_confirm_action
        self.on_save_groq_key = on_save_groq_key

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

    def confirm_action(self, confirmed: bool, manual_text: str, action_type: str, action_data_json: str):
        if self.on_confirm_action:
            try:
                data = json.loads(action_data_json) if action_data_json else {}
            except Exception:
                data = {}
            self.on_confirm_action(confirmed, manual_text, action_type, data)

    def save_groq_key(self, key: str):
        if self.on_save_groq_key:
            self.on_save_groq_key(key)

class DesktopWindowManager:
    """Manages the pywebview transparent floating desktop HUD."""

    def __init__(
        self,
        on_wake: Optional[Callable[[], None]] = None,
        on_sleep: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
        on_change_name: Optional[Callable[[str], None]] = None,
        on_confirm_action: Optional[Callable[[bool, str, str, Dict[str, Any]], None]] = None,
        on_save_groq_key: Optional[Callable[[str], None]] = None,
        width: int = 360,
        height: int = 360
    ):
        self.on_wake = on_wake
        self.on_sleep = on_sleep
        self.on_hide = on_hide
        self.on_change_name = on_change_name
        self.on_confirm_action = on_confirm_action
        self.on_save_groq_key = on_save_groq_key
        self.width = width
        self.height = height

        self.api = WindowApi(
            self._handle_wake,
            self._handle_sleep,
            self._handle_hide,
            self._handle_change_name,
            self._handle_confirm_action,
            self._handle_save_groq_key
        )
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

    def _handle_confirm_action(self, confirmed: bool, manual_text: str, action_type: str, action_data: Dict[str, Any]):
        if self.on_confirm_action:
            self.on_confirm_action(confirmed, manual_text, action_type, action_data)

    def _handle_save_groq_key(self, key: str):
        if self.on_save_groq_key:
            self.on_save_groq_key(key)

    def _apply_windows_transparency(self):
        """Applies Windows DWM glass margins and layered colorkey for 100% desktop transparency."""
        try:
            import win32gui
            import win32con
            import win32api

            class MARGINS(ctypes.Structure):
                _fields_ = [("cxLeftWidth", ctypes.c_int),
                            ("cxRightWidth", ctypes.c_int),
                            ("cyTopHeight", ctypes.c_int),
                            ("cyBottomHeight", ctypes.c_int)]

            for _ in range(40):
                time.sleep(0.1)
                hwnd = win32gui.FindWindow(None, "P.H.O.E.N.I.X.")
                if hwnd:
                    # Apply full DWM sheet-of-glass margins
                    margins = MARGINS(-1, -1, -1, -1)
                    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

                    # Set WS_EX_LAYERED
                    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED)

                    # Key out WinForms default SystemColors.Control (240, 240, 240)
                    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(240, 240, 240), 0, win32con.LWA_COLORKEY)
                    break
        except Exception as e:
            print(f"[HUD] Note: Win32 transparency hook: {e}")

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

        # Launch background thread to apply native Windows transparency attributes
        threading.Thread(target=self._apply_windows_transparency, daemon=True).start()

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
                pass

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
                pass

    def show_confirmation(self, prompt: str, target: str, action_type: str, action_data: Dict[str, Any]):
        """Displays interactive holographic confirmation & manual input card."""
        if self.window:
            safe_prompt = prompt.replace("'", "\\'").replace('"', '\\"')
            safe_target = target.replace("'", "\\'").replace('"', '\\"')
            safe_data = json.dumps(action_data).replace("'", "\\'").replace('"', '\\"')
            js = f"if (window.showConfirmationDialog) window.showConfirmationDialog('{safe_prompt}', '{safe_target}', '{action_type}', JSON.parse('{safe_data}'));"
            try:
                self.window.evaluate_js(js)
            except Exception as e:
                pass

    def hide_confirmation(self):
        """Hides holographic confirmation card."""
        if self.window:
            js = "if (window.hideConfirmationDialog) window.hideConfirmationDialog();"
            try:
                self.window.evaluate_js(js)
            except Exception as e:
                pass

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
