import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.setup_model import ensure_model_installed
from app.phoenix_app import PhoenixApp

def main():
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
