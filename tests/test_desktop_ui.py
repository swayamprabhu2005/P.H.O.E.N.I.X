import os
from unittest.mock import patch, MagicMock
from PIL import Image
from desktop.window_manager import DesktopWindowManager
from desktop.tray_manager import SystemTrayManager

def test_desktop_window_manager_create_window():
    wm = DesktopWindowManager()
    with patch("webview.create_window") as mock_create_window:
        mock_create_window.return_value = MagicMock()
        window = wm.create_window()
        assert window is not None
        mock_create_window.assert_called_once()
        kwargs = mock_create_window.call_args[1]
        assert kwargs["transparent"] is True
        # Must be valid hex triplet (6 hex digits, not 8)
        assert kwargs["background_color"] == "#000000"

def test_tray_manager_icon_image():
    tm = SystemTrayManager()
    icon_image = tm._create_icon_image()
    assert isinstance(icon_image, Image.Image)
    assert icon_image.size == (64, 64)
    assert icon_image.mode == "RGBA"
