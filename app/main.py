import ctypes
from ctypes import wintypes
import os
import sys

# 1. Set explicit Windows AppUserModelID so Windows Taskbar displays P.H.O.E.N.I.X. icon instead of generic Python icon
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Antigravity.PHOENIX.DesktopAssistant.1.1")
except Exception:
    pass

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 2. Single-instance mutex check to prevent duplicate background instances and tray icons
ERROR_ALREADY_EXISTS = 183
_single_instance_mutex = None

def acquire_single_instance() -> bool:
    global _single_instance_mutex
    try:
        kernel32 = ctypes.windll.kernel32
        CreateMutexW = kernel32.CreateMutexW
        CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
        CreateMutexW.restype = wintypes.HANDLE

        mutex = CreateMutexW(None, False, "Global\\PHOENIX_Desktop_AI_Agent_SingleInstance")
        if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
            return False
        _single_instance_mutex = mutex
        return True
    except Exception:
        return True

from app.setup_model import ensure_model_installed
from app.phoenix_app import PhoenixApp

def main():
    if not acquire_single_instance():
        print("[PHOENIX] Another instance is already running. Exiting duplicate process.")
        sys.exit(0)

    print("=" * 60)
    print("   P.H.O.E.N.I.X. — Windows Desktop AI Agent v1.1")
    print("   Personalized Holographic Operator for Execution,")
    print("   Navigation, & Interactive eXtension")
    print("=" * 60)

    # Automatically check/download Vosk model into project directory if cloned freshly from GitHub
    ensure_model_installed(project_root)

    print("Starting system tray and 3D holographic HUD...")
    app = PhoenixApp()
    app.start()

if __name__ == "__main__":
    main()
