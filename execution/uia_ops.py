import ctypes
import difflib
from collections import deque
from typing import Optional, Tuple, List
import win32con
import win32gui

try:
    import comtypes
    import comtypes.client

    comtypes.client.GetModule("UIAutomationCore.dll")
    from comtypes.gen import UIAutomationClient as UIA

    UIA_AVAILABLE = True
except Exception:
    UIA = None
    UIA_AVAILABLE = False

# Win32 SendInput constants for reliable Unicode typing & mouse wheel
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_WHEEL = 0x0800

DESTRUCTIVE_KEYWORDS = {"delete", "format", "empty trash", "empty recycle", "erase", "wipe", "uninstall"}


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", _INPUT_UNION)]


class UIAutomator:
    """
    Lightweight Windows UI Automation (UIA3) controller adapted for 4GB RAM CPU-only systems.
    Scans only the active foreground window with bounded depth/node limits.
    """

    def __init__(self, max_depth: int = 6, max_nodes: int = 150):
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self._uia = None

    def _get_uia(self):
        if not UIA_AVAILABLE:
            return None
        try:
            comtypes.CoInitialize()
        except Exception:
            pass
        if self._uia is None:
            self._uia = comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)
        return self._uia

    @staticmethod
    def _is_destructive(label: str) -> bool:
        low = label.lower()
        return any(kw in low for kw in DESTRUCTIVE_KEYWORDS)

    def _collect_foreground_elements(self) -> List[Tuple[str, object]]:
        uia = self._get_uia()
        if uia is None:
            return []

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return []

        root = uia.ElementFromHandle(hwnd)
        if not root:
            return []

        walker = uia.ControlViewWalker
        results: List[Tuple[str, object]] = []
        queue = deque([(root, 0)])
        visited = 0

        while queue and visited < self.max_nodes:
            elem, depth = queue.popleft()
            visited += 1

            try:
                name = (elem.CurrentName or "").strip()
                if name and depth > 0:
                    results.append((name, elem))
            except Exception:
                pass

            if depth >= self.max_depth:
                continue

            try:
                child = walker.GetFirstChildElement(elem)
                while child and visited + len(queue) < self.max_nodes:
                    queue.append((child, depth + 1))
                    child = walker.GetNextSiblingElement(child)
            except Exception:
                pass

        return results

    def _find_best_element(self, target_name: str, elements: List[Tuple[str, object]]) -> Optional[Tuple[str, object]]:
        query = target_name.lower().strip()
        if not query:
            return None

        best_score = 0.0
        best_match = None

        for name, elem in elements:
            low = name.lower()
            if low == query:
                return name, elem
            if query in low:
                score = 0.90 - (len(low) - len(query)) * 0.002
            else:
                score = difflib.SequenceMatcher(None, query, low).ratio()

            if score > best_score:
                best_score = score
                best_match = (name, elem)

        if best_match and best_score >= 0.65:
            return best_match
        return None

    def _invoke_element(self, elem) -> bool:
        """Tries native UIA Invoke/Selection/Toggle patterns, then falls back to bounding rect click."""
        for pattern_id, iface, method in [
            (UIA.UIA_InvokePatternId, UIA.IUIAutomationInvokePattern, "Invoke"),
            (UIA.UIA_SelectionItemPatternId, UIA.IUIAutomationSelectionItemPattern, "Select"),
            (UIA.UIA_TogglePatternId, UIA.IUIAutomationTogglePattern, "Toggle"),
        ]:
            try:
                pat_unk = elem.GetCurrentPattern(pattern_id)
                if pat_unk:
                    pat = pat_unk.QueryInterface(iface)
                    getattr(pat, method)()
                    return True
            except Exception:
                pass

        # Coordinate fallback using element's live bounding rectangle
        try:
            rect = elem.CurrentBoundingRectangle
            cx = int((rect.left + rect.right) / 2)
            cy = int((rect.top + rect.bottom) / 2)
            if cx > 0 and cy > 0:
                ctypes.windll.user32.SetCursorPos(cx, cy)
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                return True
        except Exception:
            pass
        return False

    def click_element(self, target_name: str) -> Tuple[bool, str]:
        if self._is_destructive(target_name):
            return False, f"Blocked potentially destructive click on '{target_name}' for safety."

        if not UIA_AVAILABLE:
            return False, "Windows UI Automation is unavailable."

        elements = self._collect_foreground_elements()
        match = self._find_best_element(target_name, elements)
        if not match:
            return False, f"Could not find '{target_name}' in the active window."

        matched_name, elem = match
        if self._is_destructive(matched_name):
            return False, f"Blocked potentially destructive control '{matched_name}' for safety."

        if self._invoke_element(elem):
            return True, f"Clicked {matched_name}."
        return False, f"Found '{matched_name}', but could not activate it."

    def type_text(self, text: str) -> Tuple[bool, str]:
        if not text:
            return False, "No text provided to type."

        # Try UIA ValuePattern on focused element first
        uia = self._get_uia()
        if uia is not None:
            try:
                focused = uia.GetFocusedElement()
                if focused:
                    pat_unk = focused.GetCurrentPattern(UIA.UIA_ValuePatternId)
                    if pat_unk:
                        val_pat = pat_unk.QueryInterface(UIA.IUIAutomationValuePattern)
                        if not val_pat.CurrentIsReadOnly:
                            existing = val_pat.CurrentValue or ""
                            sep = " " if existing and not existing.endswith(" ") else ""
                            val_pat.SetValue(existing + sep + text)
                            return True, f"Typed '{text}'."
            except Exception:
                pass

        # Universal Unicode SendInput fallback
        try:
            extra = ctypes.c_ulong(0)
            inputs = []
            for ch in text:
                code = ord(ch)
                down = _INPUT(type=INPUT_KEYBOARD, union=_INPUT_UNION(ki=_KEYBDINPUT(0, code, KEYEVENTF_UNICODE, 0, ctypes.pointer(extra))))
                up = _INPUT(type=INPUT_KEYBOARD, union=_INPUT_UNION(ki=_KEYBDINPUT(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))))
                inputs.extend([down, up])
            arr = (_INPUT * len(inputs))(*inputs)
            ctypes.windll.user32.SendInput(len(inputs), arr, ctypes.sizeof(_INPUT))
            return True, f"Typed '{text}'."
        except Exception as e:
            return False, f"Failed to type text: {e}"

    @staticmethod
    def scroll_active(direction: str = "down", amount: int = 360) -> Tuple[bool, str]:
        delta = -abs(amount) if direction.lower() == "down" else abs(amount)
        try:
            ctypes.windll.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, ctypes.c_ulong(delta & 0xFFFFFFFF).value, 0)
            return True, f"Scrolled {direction}."
        except Exception as e:
            return False, f"Scroll failed: {e}"

    @staticmethod
    def focus_window(title_query: str) -> Tuple[bool, str]:
        query = title_query.lower().strip()
        if not query:
            return False, "No window name provided."

        candidates = []

        def _enum_cb(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).strip()
                if title:
                    candidates.append((hwnd, title))
            return True

        win32gui.EnumWindows(_enum_cb, None)

        best_hwnd = None
        best_title = ""
        best_score = 0.0
        for hwnd, title in candidates:
            low = title.lower()
            if query in low:
                score = 0.92
            else:
                score = difflib.SequenceMatcher(None, query, low).ratio()
            if score > best_score:
                best_score = score
                best_hwnd = hwnd
                best_title = title

        if best_hwnd and best_score >= 0.55:
            try:
                if win32gui.IsIconic(best_hwnd):
                    win32gui.ShowWindow(best_hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(best_hwnd)
                return True, f"Switched to {best_title}."
            except Exception as e:
                return False, f"Could not focus '{best_title}': {e}"

        return False, f"No open window matching '{title_query}'."
