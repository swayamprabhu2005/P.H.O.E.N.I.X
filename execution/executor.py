import datetime
import json
import os
import subprocess
import webbrowser
from typing import Tuple, Dict, Any, Optional
import psutil

from commands.navigator import SystemNavigator
from execution.app_launcher import AppLauncher
from execution.file_ops import FileOperations
from execution.browser_ops import BrowserOperations
from execution.screen_ops import ScreenOperations
from execution.win_shortcuts import WindowsShortcuts

class CommandExecutor:
    """Central dispatcher executing structured intents and returning status & voice feedback."""

    def __init__(self, navigator: Optional[SystemNavigator] = None):
        self.navigator = navigator or SystemNavigator()
        self.app_launcher = AppLauncher()
        self.comet_path = r"C:\Program Files\Perplexity\Comet\Application\comet.exe"
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.settings_path = os.path.join(self.base_dir, "config", "settings.json")

    def execute(self, intent: str, params: Dict[str, Any], feedback_template: str = "") -> Tuple[bool, str, str]:
        """
        Executes given intent with extracted parameters.
        Returns: (success, display_message, speech_text)
        """
        curr_dir = self.navigator.get_current_directory()

        # 0. User Personalization
        if intent == "CHANGE_USER_NAME":
            name = params.get("name", "User").strip().title()
            try:
                if os.path.exists(self.settings_path):
                    with open(self.settings_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "user" not in data:
                        data["user"] = {}
                    data["user"]["name"] = name
                    with open(self.settings_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                return True, f"User name updated to {name}", f"Understood. I will address you as {name}."
            except Exception as e:
                return False, f"Could not update name: {e}", "Could not update user name."

        # 1. Terminals & Command Prompt
        elif intent == "OPEN_CMD":
            try:
                subprocess.Popen("cmd.exe", shell=True)
                return True, "Opened Command Prompt", "Opening Command Prompt."
            except Exception as e:
                return False, f"Failed to open CMD: {e}", "Could not open Command Prompt."

        elif intent == "OPEN_POWERSHELL":
            try:
                subprocess.Popen("powershell.exe", shell=True)
                return True, "Opened PowerShell", "Opening PowerShell."
            except Exception as e:
                return False, f"Failed to open PowerShell: {e}", "Could not open PowerShell."

        # 2. Specialized Modes (Coding & Learning)
        elif intent == "CODING_MODE_VSCODE":
            ok = self.app_launcher.launch("code")
            if not ok:
                try:
                    subprocess.Popen("code", shell=True)
                    ok = True
                except Exception:
                    ok = False
            if ok:
                return True, "Coding mode: VS Code launched", "Coding mode VS Code activated."
            return False, "VS Code not found on system", "VS Code not found."

        elif intent == "CODING_MODE_ANTIGRAVITY":
            ok = self.app_launcher.launch("antigravity")
            if not ok:
                try:
                    subprocess.Popen("antigravity", shell=True)
                    ok = True
                except Exception:
                    ok = False
            if ok:
                return True, "Coding mode: Antigravity launched", "Coding mode Antigravity activated."
            return False, "Antigravity not found in path", "Antigravity not found."

        elif intent == "LEARNING_MODE_CHATGPT":
            webbrowser.open("https://chatgpt.com")
            return True, "Learning mode: Opened ChatGPT", "Opening ChatGPT."

        elif intent == "LEARNING_MODE_PERPLEXITY":
            # Per user request: open Comet Browser specifically for Perplexity!
            if os.path.exists(self.comet_path):
                subprocess.Popen([self.comet_path, "https://www.perplexity.ai"])
                return True, "Opened Perplexity on Comet Browser", "Opening Perplexity on Comet Browser."
            else:
                webbrowser.open("https://www.perplexity.ai")
                return True, "Opened Perplexity AI", "Opening Perplexity AI."

        # 3. Google Services & Dynamic Multi-Account Switching
        elif intent == "OPEN_EMAIL":
            webbrowser.open("https://mail.google.com")
            return True, "Opened Gmail", "Opening Gmail."

        elif intent == "OPEN_GOOGLE_DRIVE":
            webbrowser.open("https://drive.google.com")
            return True, "Opened Google Drive", "Opening Google Drive."

        elif intent == "SWITCH_GOOGLE_ACCOUNT_NUM":
            num_str = params.get("num", "1")
            try:
                account_num = int(num_str)
                idx = max(0, account_num - 1)
            except ValueError:
                account_num = 1
                idx = 0
            target_url = f"https://mail.google.com/mail/u/{idx}/"
            webbrowser.open(target_url)
            return True, f"Switched to Google Account {account_num} (/u/{idx}/)", f"Switched to account {account_num}."

        elif intent == "SWITCH_GOOGLE_ACCOUNT_CHOOSER":
            webbrowser.open("https://accounts.google.com/AccountChooser")
            return True, "Opened Google Account Chooser", "Opening Google account chooser."

        # 4. Open File by Name (PDF, Word, TXT, PPT)
        elif intent == "OPEN_PDF_FILE":
            name = params.get("name", "")
            ok, msg = FileOperations.open_file_by_name(curr_dir, name, ".pdf")
            speech = f"Opening PDF {name}." if ok else f"Could not find PDF {name}."
            return ok, msg, speech

        elif intent == "OPEN_WORD_FILE":
            name = params.get("name", "")
            ok, msg = FileOperations.open_file_by_name(curr_dir, name, ".docx")
            speech = f"Opening Word file {name}." if ok else f"Could not find Word file {name}."
            return ok, msg, speech

        elif intent == "OPEN_TXT_FILE":
            name = params.get("name", "")
            ok, msg = FileOperations.open_file_by_name(curr_dir, name, ".txt")
            speech = f"Opening text file {name}." if ok else f"Could not find text file {name}."
            return ok, msg, speech

        elif intent == "OPEN_PPT_FILE":
            name = params.get("name", "")
            ok, msg = FileOperations.open_file_by_name(curr_dir, name, ".pptx")
            speech = f"Opening presentation {name}." if ok else f"Could not find presentation {name}."
            return ok, msg, speech

        # 5. Navigation Commands
        elif intent == "OPEN_EXPLORER":
            ok = self.navigator.sync_explorer()
            return ok, f"Opened Explorer at {curr_dir}", "Opening File Explorer."

        elif intent == "NAVIGATE_DRIVE":
            drive = params.get("drive", "C")
            ok = self.navigator.navigate_drive(drive)
            if ok:
                return True, f"Navigated to {drive.upper()}:\\", f"Navigated to {drive.upper()} drive."
            return False, f"Drive {drive.upper()}: not found", f"{drive.upper()} drive not available."

        elif intent == "OPEN_FOLDER":
            name = params.get("name", "")
            ok = self.navigator.open_folder(name)
            new_dir = self.navigator.get_current_directory()
            if ok:
                return True, f"Opened folder: {new_dir}", f"Opened folder {name}."
            return False, f"Folder '{name}' not found in {curr_dir}", f"Folder {name} not found."

        elif intent == "GO_BACK":
            ok = self.navigator.go_back()
            new_dir = self.navigator.get_current_directory()
            if ok:
                return True, f"Moved back to: {new_dir}", "Going back."
            return False, "Cannot go back any further", "Already at root."

        # 6. File and Folder Creation
        elif intent == "CREATE_FOLDER":
            name = params.get("name", "New Folder")
            ok, msg = FileOperations.create_folder(curr_dir, name)
            speech = f"Folder {name} created." if ok else "Could not create folder."
            return ok, msg, speech

        elif intent == "CREATE_TXT_FILE":
            name = params.get("name", "notes")
            ok, msg = FileOperations.create_text_file(curr_dir, name)
            speech = f"Text file {name} created." if ok else "Could not create text file."
            return ok, msg, speech

        elif intent == "CREATE_WORD_FILE":
            name = params.get("name", "document")
            ok, msg = FileOperations.create_word_file(curr_dir, name)
            speech = f"Word file {name} created." if ok else "Could not create Word document."
            return ok, msg, speech

        elif intent == "CREATE_FILE":
            name = params.get("name", "file.txt")
            ok, msg = FileOperations.create_generic_file(curr_dir, name)
            speech = f"File {name} created." if ok else "Could not create file."
            return ok, msg, speech

        elif intent == "RENAME_ITEM":
            old_name = params.get("old_name", "")
            new_name = params.get("new_name", "")
            ok, msg = FileOperations.rename_item(curr_dir, old_name, new_name)
            speech = f"Renamed to {new_name}." if ok else "Failed to rename item."
            return ok, msg, speech

        # 7. Application Launch
        elif intent == "OPEN_APP":
            app = params.get("app", "")
            ok = self.app_launcher.launch(app)
            if ok:
                return True, f"Launched {app.title()}", f"Opening {app}."
            return False, f"Could not launch {app}", f"{app} not found."

        # 8. Browser Control & Web Search
        elif intent == "COPY_URL":
            ok, result = BrowserOperations.copy_browser_url()
            if ok:
                return True, f"Copied URL: {result[:50]}...", "URL copied to clipboard."
            return False, result, "Could not copy URL."

        elif intent == "WEB_SEARCH":
            query = params.get("query", "")
            ok = BrowserOperations.search_google(query)
            return ok, f"Searching Google for '{query}'", f"Searching for {query}."

        elif intent == "NEW_TAB":
            WindowsShortcuts.new_tab()
            return True, "Opened new browser tab", "New tab."

        elif intent == "CLOSE_TAB":
            WindowsShortcuts.close_tab()
            return True, "Closed browser tab", "Tab closed."

        elif intent == "REOPEN_TAB":
            WindowsShortcuts.reopen_tab()
            return True, "Reopened closed browser tab", "Tab restored."

        elif intent == "BOOKMARK_PAGE":
            WindowsShortcuts.bookmark_page()
            return True, "Bookmarked page", "Bookmarked."

        # 9. Documents Navigation
        elif intent == "NEXT_PAGE":
            WindowsShortcuts.next_page()
            return True, "Next page", "Next page."

        elif intent == "PREV_PAGE":
            WindowsShortcuts.prev_page()
            return True, "Previous page", "Previous page."

        # 10. Screen Ops (Downloads folder + Clipboard)
        elif intent == "TAKE_SCREENSHOT":
            ok, path = ScreenOperations.take_screenshot()
            if ok:
                filename = os.path.basename(path)
                return True, f"Screenshot saved to Downloads: {filename}", "Screenshot captured."
            return False, path, "Screenshot failed."

        elif intent == "SNIPPING_TOOL":
            ok = ScreenOperations.activate_snipping_tool()
            return ok, "Snipping Tool activated", "Snipping Tool activated."

        # 11. Windows Shortcuts
        elif intent == "SHOW_DESKTOP":
            WindowsShortcuts.show_desktop()
            return True, "Toggled Desktop", "Showing desktop."

        elif intent == "OPEN_CLIPBOARD":
            WindowsShortcuts.open_clipboard_history()
            return True, "Opened Clipboard History", "Clipboard opened."

        elif intent == "LOCK_PC":
            WindowsShortcuts.lock_workstation()
            return True, "Locked workstation", "Workstation locked."

        elif intent == "MAXIMIZE_WINDOW":
            WindowsShortcuts.maximize_window()
            return True, "Maximized window", "Maximized."

        elif intent == "SNAP_LEFT":
            WindowsShortcuts.snap_left()
            return True, "Snapped window left", "Snapped left."

        elif intent == "SNAP_RIGHT":
            WindowsShortcuts.snap_right()
            return True, "Snapped window right", "Snapped right."

        elif intent == "VOLUME_UP":
            WindowsShortcuts.volume_up()
            return True, "Volume increased", "Volume up."

        elif intent == "VOLUME_DOWN":
            WindowsShortcuts.volume_down()
            return True, "Volume decreased", "Volume down."

        elif intent == "MUTE_VOLUME":
            WindowsShortcuts.toggle_mute()
            return True, "Toggled audio mute", "Audio mute toggled."

        elif intent == "WHAT_TIME":
            now = datetime.datetime.now()
            time_formatted = now.strftime("%I:%M %p").lstrip("0")
            return True, f"Current time: {time_formatted}", f"It is {time_formatted}."

        elif intent == "BATTERY_STATUS":
            battery = psutil.sensors_battery()
            if battery:
                percent = int(battery.percent)
                plugged = "plugged in" if battery.power_plugged else "on battery"
                return True, f"Battery: {percent}% ({plugged})", f"Battery is at {percent} percent, {plugged}."
            return True, "Desktop system without battery", "No battery detected."

        # 12. Custom Dynamic Actions added via tools/add_feature.py
        elif intent.startswith("CUSTOM_"):
            return True, f"Executed custom automation: {intent}", feedback_template

        return False, "Unsupported command.", "I could not perform that action."
