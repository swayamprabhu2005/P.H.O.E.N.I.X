import json
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    registry_path = os.path.join(base_dir, "commands", "command_registry.json")
    whitelist_path = os.path.join(base_dir, "config", "apps_whitelist.json")

    print("=" * 60)
    print("   P.H.O.E.N.I.X. Dynamic Feature & Automation Creator")
    print("=" * 60)
    print("Add new custom voice commands and desktop automations in seconds.\n")

    # 1. Spoken trigger phrase
    phrase = input("Enter spoken voice trigger (e.g. 'open antigravity'): ").strip()
    if not phrase:
        print("[ERROR] Trigger phrase cannot be empty.")
        return

    # 2. Action type
    print("\nSelect Action Type:")
    print("  1. Launch Desktop Application (.exe)")
    print("  2. Open Website / Web URL")
    print("  3. Run Command Prompt / Terminal Command")
    print("  4. Run Custom Script (.bat, .ps1, .py)")
    choice = input("Enter choice (1-4) [default 1]: ").strip() or "1"

    action_type = "executable"
    target_cmd = ""
    uri = ""

    if choice == "1":
        action_type = "executable"
        target_cmd = input("Enter application executable path or name (e.g. antigravity.exe): ").strip()
    elif choice == "2":
        action_type = "url"
        uri = input("Enter website URL (e.g. https://www.google.com): ").strip()
        if not uri.startswith("http://") and not uri.startswith("https://"):
            uri = "https://" + uri
    elif choice == "3":
        action_type = "command"
        target_cmd = input("Enter terminal command (e.g. cmd.exe /k dir): ").strip()
    elif choice == "4":
        action_type = "script"
        target_cmd = input("Enter script path (.bat, .ps1, .py): ").strip()
    else:
        print("[ERROR] Invalid selection.")
        return

    # 3. Confirmation feedback
    feedback = input("\nEnter assistant voice confirmation (e.g. 'Opening Antigravity.'): ").strip()
    if not feedback:
        feedback = f"Executing {phrase}."

    # Unique intent key
    clean_id = phrase.upper().replace(" ", "_").replace("-", "_")
    intent_id = f"CUSTOM_{clean_id}"

    # Load existing registry
    with open(registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    # Check if pattern already exists
    new_intent_entry = {
        "intent": intent_id,
        "patterns": [phrase.lower()],
        "params": {},
        "feedback": feedback,
        "custom": {
            "type": action_type,
            "target": target_cmd or uri
        }
    }
    registry_data["intents"].append(new_intent_entry)

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2)

    # Also register in apps_whitelist if application type
    if action_type == "executable" and os.path.exists(whitelist_path):
        with open(whitelist_path, "r", encoding="utf-8") as f:
            whitelist_data = json.load(f)
        whitelist_data[phrase.lower()] = {
            "type": "executable",
            "command": target_cmd
        }
        with open(whitelist_path, "w", encoding="utf-8") as f:
            json.dump(whitelist_data, f, indent=2)

    print("\n" + "=" * 60)
    print(f" [SUCCESS] Custom feature registered successfully!")
    print(f" Voice Trigger: \"{phrase}\"")
    print(f" Action: {action_type} -> {target_cmd or uri}")
    print(f" Voice Feedback: \"{feedback}\"")
    print("=" * 60)
    print("P.H.O.E.N.I.X. will now recognize this command automatically.\n")

if __name__ == "__main__":
    main()
