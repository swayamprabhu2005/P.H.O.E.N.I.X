import os
import threading
from typing import Callable, Optional
from PIL import Image, ImageDraw
import pystray

class SystemTrayManager:
    """Manages the Windows notification area tray icon and context menu."""

    def __init__(
        self,
        on_show: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None,
        on_wake: Optional[Callable[[], None]] = None,
        on_sleep: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None
    ):
        self.on_show = on_show
        self.on_hide = on_hide
        self.on_wake = on_wake
        self.on_sleep = on_sleep
        self.on_exit = on_exit

        self.icon = None
        self._thread = None

    def _create_icon_image(self) -> Image.Image:
        """Loads the official P.H.O.E.N.I.X. logo or generates fallback fiery orb."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate_paths = [
            os.path.join(base_dir, "assets", "logo.png"),
            os.path.join(base_dir, "visual", "logo.png"),
            os.path.join(base_dir, "assets", "phoenix.ico"),
            os.path.join(base_dir, "phoenix.ico"),
        ]

        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    with Image.open(path) as img:
                        return img.convert("RGBA").resize((64, 64), Image.Resampling.LANCZOS)
                except Exception:
                    pass

        # Fallback procedural icon
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Concentric glowing rings
        draw.ellipse([4, 4, 60, 60], outline=(255, 80, 0, 180), width=3)
        draw.ellipse([12, 12, 52, 52], outline=(255, 140, 0, 220), width=4)
        draw.ellipse([20, 20, 44, 44], fill=(255, 180, 0, 255))
        draw.ellipse([26, 26, 38, 38], fill=(255, 255, 255, 255))

        return img

    def start(self):
        """Starts the system tray in a background thread."""
        image = self._create_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("Show P.H.O.E.N.I.X.", lambda icon, item: self.on_show and self.on_show(), default=True),
            pystray.MenuItem("Hide P.H.O.E.N.I.X.", lambda icon, item: self.on_hide and self.on_hide()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Wake Up", lambda icon, item: self.on_wake and self.on_wake()),
            pystray.MenuItem("Standby / Sleep", lambda icon, item: self.on_sleep and self.on_sleep()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit P.H.O.E.N.I.X.", lambda icon, item: self.on_exit and self.on_exit())
        )

        self.icon = pystray.Icon("PHOENIX", image, "P.H.O.E.N.I.X. Desktop Assistant", menu)

        self._thread = threading.Thread(target=self.icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.icon:
            try:
                self.icon.visible = False
                self.icon.stop()
            except Exception:
                pass
            self.icon = None
