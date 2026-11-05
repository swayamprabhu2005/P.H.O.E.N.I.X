import time
import urllib.parse
import webbrowser
import win32gui
import win32con
import win32clipboard
from execution.win_shortcuts import WindowsShortcuts, hotkey_ctrl

class BrowserOperations:
    """Handles browser automation, Google Search, and URL copying to clipboard."""

    @staticmethod
    def _find_browser_window():
        """Finds Chrome or Edge window handle."""
        found_hwnd = None

        def enum_windows_callback(hwnd, extra):
            nonlocal found_hwnd
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                class_name = win32gui.GetClassName(hwnd)
                if ("chrome" in title or "edge" in title or 
                    "google chrome" in title or "microsoft edge" in title):
                    found_hwnd = hwnd
                    return False
            return True

        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception:
            pass

        return found_hwnd

    @staticmethod
    def copy_browser_url() -> tuple[bool, str]:
        """Focuses browser window, presses Ctrl+L and Ctrl+C, and reads the clipboard."""
        hwnd = BrowserOperations._find_browser_window()
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.15)
            except Exception as e:
                print(f"Could not bring window to foreground: {e}")

        # Send Ctrl+L to focus address bar
        hotkey_ctrl(ord('L'))
        time.sleep(0.15)
        # Send Ctrl+C to copy
        hotkey_ctrl(ord('C'))
        time.sleep(0.15)

        # Read clipboard
        url = ""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                url = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            win32clipboard.CloseClipboard()
        except Exception as e:
            return False, f"Could not read clipboard: {e}"

        if url and (url.startswith("http://") or url.startswith("https://") or "www." in url or "." in url):
            return True, url
        elif url:
            return True, url
        else:
            return False, "No URL detected on clipboard."

    @staticmethod
    def search_google(query: str) -> bool:
        """Searches Google for the specified text query in default browser."""
        safe_query = urllib.parse.quote(query.strip())
        url = f"https://www.google.com/search?q={safe_query}"
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"Failed to open web search: {e}")
            return False
