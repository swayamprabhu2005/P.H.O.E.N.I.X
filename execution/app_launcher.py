import json
import os
import subprocess
from typing import Optional

class AppLauncher:
    """Safely launches authorized Windows desktop applications."""

    def __init__(self, whitelist_path: Optional[str] = None):
        if whitelist_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            whitelist_path = os.path.join(base_dir, "config", "apps_whitelist.json")

        self.whitelist = {}
        if os.path.exists(whitelist_path):
            with open(whitelist_path, "r", encoding="utf-8") as f:
                self.whitelist = json.load(f)

    def launch(self, app_name: str) -> bool:
        normalized = app_name.strip().lower()
        if normalized not in self.whitelist:
            # Attempt direct execution of well-known name
            try:
                os.startfile(normalized)
                return True
            except Exception:
                return False

        config = self.whitelist[normalized]
        app_type = config.get("type", "executable")

        if app_type == "protocol":
            command = config.get("command") or config.get("uri")
            try:
                os.startfile(command)
                return True
            except Exception as e:
                print(f"Failed to launch protocol {command}: {e}")
                return False

        # Executable
        cmd = config.get("command", "")
        # Try direct command first
        try:
            subprocess.Popen(cmd, shell=True)
            return True
        except Exception:
            pass

        # Try fallback paths
        for path in config.get("fallback_paths", []):
            if os.path.exists(path):
                subprocess.Popen([path])
                return True

        return False
