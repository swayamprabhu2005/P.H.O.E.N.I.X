# P.H.O.E.N.I.X. — Architecture, Feature Roadmap & Implementation Plan (v3.0)

**Assistant:** P.H.O.E.N.I.X. (Personalized Holographic Operator for Execution, Navigation, & Interactive eXtension)  
**Status:** Completed, Hardened & Verified  
**Target Platform:** Windows 10 / Windows 11 (64-bit), 4 GB RAM, CPU-only  

---

## 1. 3D Holographic Dyson Sphere Core Architecture (v3.0)

1. **Compacted Dyson Geometry with Zero Viewport Clipping:**
   - **20 multi-axis interlocking toroids** forming a dense, continuous 360-degree spherical cage.
   - Radii tightly bounded between $r = 1.85$ and $3.68$ units with tube thicknesses $0.050 - 0.065$.
   - Camera configured at $Z = 13.8$ with $45^\circ$ FOV, ensuring the entire 3D structure and its particle embers maintain generous padding inside the 340px canvas with **zero boundary clipping** in all rotational orientations.
   - Rotational speed increased for high-responsiveness during awake, listening, and processing states.

2. **Top-to-Bottom Gradual Ultron Blue Wave Transition:**
   - **Awake State:** Blazing holographic amber, fiery molten orange (`#ff5500` - `#ff9900`), and white-hot nuclear core with high rotation speed.
   - **Sleep State:** When the user commands *"stop"* or *"go to sleep"*, the sphere begins a smooth, top-to-bottom wave cascade.
   - Rings and particle embers gradually cool into **Ultron Blue / electric cyan** (`#00d4ff`, `#00a8ff`, `#0055ff`), lights dim to a soft slumber glow, core rotation eases to a calm idle, and voice recognition is paused.
   - **Awakening:** Clicking the 3D core awakens P.H.O.E.N.I.X., transitions back to vibrant fiery orange, and greets the user personally: *"At your service, Swayam."*

3. **100% Transparent Borderless Desktop Overlay:**
   - The pywebview window is frameless, top-most (`on_top=True`), and completely transparent (`background_color="#00000000"`).
   - Floats directly over any application (Chrome, IDE, Word, desktop wallpaper) as a pure circular holographic entity.
   - Full native drag support allows moving the widget anywhere on the desktop.

---

## 2. Voice Recognition & Strict Silent Rejection

1. **100% Offline Local Vosk Engine:**
   - Stored strictly within the project folder: `models/vosk-model-small-en-us-0.15`.
   - Never downloads outside the local workspace root.
2. **Strict Silent Rejection of Ambient Speech:**
   - When awake, P.H.O.E.N.I.X. filters spoken sentences against the registered command list.
   - If spoken words do not match any registered command intent, P.H.O.E.N.I.X. **silently ignores them** with zero spoken errors and zero intrusive toasts, allowing normal conversation in the room without interruptions.
3. **Personalized Greeting:**
   - Configurable name in `config/settings.json` (defaults to Swayam).
   - Greet on startup and on wake: *"At your service, Swayam."*
   - Change name dynamically via voice: *"Call me Swayam"* or *"Change my name to [Name]"*.

---

## 3. Registered Voice Operations Suite

### A. Lifecycle & Sleep
- *"Stop"* / *"Go to sleep"* / *"Sleep"* / *"Standby"*: Triggers top-to-bottom Ultron Blue transition and stops microphone.
- *"Shutdown"* / *"Close Phoenix"* / *"Exit"*: Clean application termination.
- *Click Core*: Awakens assistant, plays *"At your service, Swayam"*, and starts microphone.

### B. Specialized Modes & Browsers
- *"Coding mode VS Code"*: Launches Visual Studio Code.
- *"Coding mode Antigravity"*: Launches Antigravity IDE.
- *"Learning mode ChatGPT"*: Opens `https://chatgpt.com` in default browser.
- *"Learning mode Perplexity"* / *"Meeting mode Perplexity"*: Opens **Comet Browser** (`C:\Program Files\Perplexity\Comet\Application\comet.exe`) directly to Perplexity AI.

### C. Google Suite & Multi-Account Switching
- *"Open Email"* / *"Open Gmail"*: Opens Gmail in Chrome/default browser.
- *"Open Google Drive"* / *"Open Drive"*: Opens Google Drive in Chrome/default browser.
- *"Switch to account {N}"* / *"Account {N}"* (e.g. 1, 2, 3, 4, 5): Navigates directly to Google user profile `/u/{N-1}/`.
- *"Switch account"* / *"Account chooser"*: Opens Google Account Chooser.

### D. File Navigation & Operations by Name
- *"Open PDF [name]"*: Opens matching `.pdf` file in active directory.
- *"Open Word [name]"*: Opens matching `.docx`/`.doc` file in active directory.
- *"Open Text [name]"* / *"Open TXT [name]"*: Opens matching `.txt` file in active directory.
- *"Open Presentation [name]"* / *"Open PPT [name]"*: Opens matching `.pptx` presentation in active directory.
- *"Create Folder [name]"*: Creates directory.
- *"Create Text File [name]"*: Creates `.txt` file.
- *"Create Word File [name]"*: Creates `.docx` file.
- *"Rename [old] to [new]"*: Renames file or folder.
- *"Go to [drive] drive"* / *"Open folder [name]"* / *"Go back"*: Live explorer navigation.

### E. Screen Capture to Downloads
- *"Take screenshot"*: Captures screen directly into **`Downloads/Screenshot_YYYYMMDD_HHMMSS.png`** and copies it to clipboard.
- *"Activate Snipping Tool"*: Opens Windows Snipping Tool.

### F. Desktop & Windows Shortcuts
- *"Show desktop"*: Minimizes all windows (`Win+D`).
- *"Open clipboard"*: Opens clipboard history (`Win+V`).
- *"Lock PC"*: Locks workstation (`Win+L`).
- *"Next page"* / *"Previous page"*: Sends `Page_Down` / `Page_Up`.
- *"Volume up"* / *"Volume down"* / *"Mute"*: Audio control.
- *"What time is it"* / *"Check battery"*: Real-time spoken system status.
- *"Open Command Prompt"* / *"Open PowerShell"*: Launches CLI environments.
- *"Search [query]"*: Direct Google search.
- *"Copy URL"*: Focuses address bar and copies URL to clipboard.

---

## 4. Setup, Installer & Extensibility

- **One-Click Startup:** `run.bat` automatically verifies dependencies, downloads the Vosk model into `models/` on first run, and launches the application.
- **Dynamic Feature Extensibility:** `add_feature.bat` (`tools/add_feature.py`) CLI wizard allowing anyone to add new custom voice commands and system actions without touching Python code.
- **Standalone Windows Installer:** Inno Setup script (`installer/phoenix_installer.iss`) and `installer/build_installer.bat` to compile a single `.exe` installer.
