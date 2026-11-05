import os
import subprocess
from typing import Optional

class SystemNavigator:
    """Maintains active working directory state and synchronizes with Windows File Explorer."""

    def __init__(self, initial_directory: Optional[str] = None):
        if initial_directory and os.path.exists(initial_directory):
            self.current_directory = os.path.abspath(initial_directory)
        else:
            # Default to User's Desktop
            user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(user_desktop):
                self.current_directory = user_desktop
            else:
                self.current_directory = os.path.abspath("C:\\")

    def get_current_directory(self) -> str:
        return self.current_directory

    def sync_explorer(self) -> bool:
        """Opens or synchronizes Windows File Explorer at current_directory."""
        try:
            if os.path.exists(self.current_directory):
                subprocess.Popen(["explorer.exe", self.current_directory])
                return True
        except Exception as e:
            print(f"Error syncing explorer: {e}")
        return False

    def navigate_drive(self, drive_letter: str) -> bool:
        """Navigates to a specific drive root (e.g. C:, D:)."""
        drive = drive_letter.upper().strip(":\\") + ":\\"
        if os.path.exists(drive):
            self.current_directory = drive
            self.sync_explorer()
            return True
        return False

    def open_folder(self, folder_name: str) -> bool:
        """Opens a subfolder in current directory, preserving exact filesystem casing."""
        target_name = folder_name.strip()

        # Check children by exact case-insensitive match first to preserve filesystem casing
        try:
            for item in os.listdir(self.current_directory):
                if item.lower() == target_name.lower():
                    full_path = os.path.join(self.current_directory, item)
                    if os.path.isdir(full_path):
                        self.current_directory = full_path
                        self.sync_explorer()
                        return True
        except PermissionError:
            return False

        # Fallback to direct path check
        direct_path = os.path.join(self.current_directory, target_name)
        if os.path.isdir(direct_path):
            self.current_directory = direct_path
            self.sync_explorer()
            return True

        return False

    def go_back(self) -> bool:
        """Navigates to parent directory."""
        parent = os.path.dirname(self.current_directory.rstrip("\\/"))
        if parent and os.path.exists(parent):
            self.current_directory = parent
            self.sync_explorer()
            return True
        return False

    def resolve_path(self, item_name: str) -> str:
        """Returns full absolute path inside current directory."""
        return os.path.join(self.current_directory, item_name.strip())
