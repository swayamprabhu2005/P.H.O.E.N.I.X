import ctypes
import time

user32 = ctypes.windll.user32

# Virtual Key Codes
VK_LWIN = 0x5B
VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_MENU = 0x12  # Alt
VK_RETURN = 0x0D
VK_UP = 0x26
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_PRIOR = 0x21  # Page Up
VK_NEXT = 0x22   # Page Down
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF

KEYEVENTF_KEYUP = 0x0002

def press_key(vk_code: int):
    user32.keybd_event(vk_code, 0, 0, 0)

def release_key(vk_code: int):
    user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)

def tap_key(vk_code: int, delay: float = 0.05):
    press_key(vk_code)
    time.sleep(delay)
    release_key(vk_code)

def hotkey_win(vk_code: int):
    press_key(VK_LWIN)
    time.sleep(0.05)
    tap_key(vk_code)
    release_key(VK_LWIN)

def hotkey_ctrl(vk_code: int):
    press_key(VK_CONTROL)
    time.sleep(0.05)
    tap_key(vk_code)
    release_key(VK_CONTROL)

def hotkey_ctrl_shift(vk_code: int):
    press_key(VK_CONTROL)
    press_key(VK_SHIFT)
    time.sleep(0.05)
    tap_key(vk_code)
    release_key(VK_SHIFT)
    release_key(VK_CONTROL)

class WindowsShortcuts:
    """Provides native Windows hotkeys and system automation."""

    @staticmethod
    def show_desktop():
        hotkey_win(ord('D'))

    @staticmethod
    def open_clipboard_history():
        hotkey_win(ord('V'))

    @staticmethod
    def open_settings():
        hotkey_win(ord('I'))

    @staticmethod
    def lock_workstation():
        user32.LockWorkStation()

    @staticmethod
    def maximize_window():
        hotkey_win(VK_UP)

    @staticmethod
    def snap_left():
        hotkey_win(VK_LEFT)

    @staticmethod
    def snap_right():
        hotkey_win(VK_RIGHT)

    @staticmethod
    def next_page():
        tap_key(VK_NEXT)

    @staticmethod
    def prev_page():
        tap_key(VK_PRIOR)

    @staticmethod
    def new_tab():
        hotkey_ctrl(ord('T'))

    @staticmethod
    def close_tab():
        hotkey_ctrl(ord('W'))

    @staticmethod
    def reopen_tab():
        hotkey_ctrl_shift(ord('T'))

    @staticmethod
    def bookmark_page():
        hotkey_ctrl(ord('D'))

    @staticmethod
    def volume_up(steps: int = 2):
        for _ in range(steps):
            tap_key(VK_VOLUME_UP, 0.02)

    @staticmethod
    def volume_down(steps: int = 2):
        for _ in range(steps):
            tap_key(VK_VOLUME_DOWN, 0.02)

    @staticmethod
    def toggle_mute():
        tap_key(VK_VOLUME_MUTE)
