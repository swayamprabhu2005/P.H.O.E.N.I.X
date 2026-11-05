import datetime
import io
import os
import subprocess
from typing import Tuple
from PIL import ImageGrab
import win32clipboard
import win32con

class ScreenOperations:
    """Manages full screen captures and Snipping Tool execution."""

    @staticmethod
    def _send_image_to_clipboard(image):
        """Sends a PIL image to Windows clipboard as DIB."""
        output = io.BytesIO()
        image.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Remove 14-byte BMP header to get DIB
        output.close()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()

    @staticmethod
    def take_screenshot() -> Tuple[bool, str]:
        """Captures full screen, saves to Downloads folder and copies to clipboard."""
        try:
            # User specifically requested Downloads folder
            user_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
            os.makedirs(user_downloads, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Screenshot_{timestamp}.png"
            filepath = os.path.join(user_downloads, filename)

            # Capture full screen
            screenshot = ImageGrab.grab(all_screens=True)
            screenshot.save(filepath, "PNG")

            # Copy to clipboard
            try:
                ScreenOperations._send_image_to_clipboard(screenshot)
            except Exception as e:
                print(f"Could not copy screenshot to clipboard: {e}")

            return True, filepath
        except Exception as e:
            return False, f"Screenshot failed: {e}"

    @staticmethod
    def activate_snipping_tool() -> bool:
        """Launches the Windows Snipping Tool."""
        try:
            subprocess.Popen("snippingtool.exe", shell=True)
            return True
        except Exception as e:
            print(f"Failed to launch Snipping Tool: {e}")
            return False
