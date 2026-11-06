import json
import os
import subprocess
import sys
import time
from app.setup_model import ensure_model_installed

def run_first_time_setup():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    print("=" * 64)
    print("   P.H.O.E.N.I.X. — First-Time Configuration & Personalization")
    print("   Personalized Holographic Operator for Execution,")
    print("   Navigation, & Interactive eXtension")
    print("=" * 64)
    print()

    # 1. Dependency verification
    print("[1/3] Verifying and configuring dependencies...")
    required_packages = [
        "pywebview", "vosk", "sounddevice", "pyttsx3",
        "pywin32", "pillow", "psutil"
    ]
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"   Installing missing packages: {', '.join(missing)}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)
            print("   [SUCCESS] Packages installed successfully.")
        except Exception as e:
            print(f"   [WARNING] Could not auto-install packages: {e}")
    else:
        print("   [SUCCESS] All core packages are verified.")

    # 2. Vosk model verification
    try:
        ensure_model_installed(project_root)
    except Exception as e:
        print(f"   [WARNING] Voice model check: {e}")

    # Load existing settings
    config_dir = os.path.join(project_root, "config")
    os.makedirs(config_dir, exist_ok=True)
    settings_path = os.path.join(config_dir, "settings.json")

    settings = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}

    current_name = settings.get("user", {}).get("name", "").strip()
    current_key = settings.get("ai", {}).get("groq_api_key", "").strip()

    print()
    print("[2/3] Personalization")
    prompt_name = f"   What should P.H.O.E.N.I.X. call you? "
    if current_name:
        prompt_name += f"[Default: {current_name}]: "
    else:
        prompt_name += "[e.g. Swayam]: "

    user_input_name = input(prompt_name).strip()
    chosen_name = user_input_name.title() if user_input_name else (current_name or "Operator")

    if "user" not in settings:
        settings["user"] = {}
    settings["user"]["name"] = chosen_name
    print(f"   -> Personalized operator set to: {chosen_name}")

    print()
    print("[3/3] Groq Cloud AI Integration (Optional)")
    print("   Enables smart disambiguation for open web searches, websites, and file operations.")
    if current_key:
        masked = current_key[:4] + "..." + current_key[-4:]
        prompt_key = f"   Enter Groq API Key [Press Enter to keep {masked}]: "
    else:
        prompt_key = "   Enter Groq API Key [Press Enter to skip and use offline mode]: "

    user_input_key = input(prompt_key).strip()
    chosen_key = user_input_key if user_input_key else current_key

    if "ai" not in settings:
        settings["ai"] = {}
    settings["ai"]["groq_api_key"] = chosen_key
    settings["ai"]["groq_model"] = settings.get("ai", {}).get("groq_model", "llama-3.3-70b-versatile")

    if chosen_key:
        print("   -> Groq Cloud AI: Enabled")
    else:
        print("   -> Groq Cloud AI: Skipped (Offline mode enabled)")

    # Save settings
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)

    # Create .setup_done marker
    setup_marker = os.path.join(config_dir, ".setup_done")
    with open(setup_marker, "w", encoding="utf-8") as f:
        f.write(f"Setup completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    print()
    print("=" * 64)
    print("   [SUCCESS] Setup completed! Launching P.H.O.E.N.I.X. ...")
    print("=" * 64)
    time.sleep(1.2)

if __name__ == "__main__":
    run_first_time_setup()
