# P.H.O.E.N.I.X.
### **Personalized Holographic Operator for Execution, Navigation, & Interactive eXtension**

[![Download for Windows](https://img.shields.io/badge/Download-Windows%20Setup%20(.exe)-00e575?style=for-the-badge&logo=windows&logoColor=041008)](https://github.com/swayamprabhu2005/P.H.O.E.N.I.X./releases/latest/download/PHOENIX_Setup.exe)
[![Live Web Showcase](https://img.shields.io/badge/Live%20Showcase-GitHub%20Pages-10b981?style=for-the-badge&logo=githubpages&logoColor=white)](https://swayamprabhu2005.github.io/P.H.O.E.N.I.X./)
[![Release](https://img.shields.io/badge/Release-v1.0.0-34d399?style=for-the-badge)](https://github.com/swayamprabhu2005/P.H.O.E.N.I.X./releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-f8fafc?style=for-the-badge)](installer/LICENSE.txt)

> **Live Showcase Website:** [https://swayamprabhu2005.github.io/P.H.O.E.N.I.X./](https://swayamprabhu2005.github.io/P.H.O.E.N.I.X./)  
> **Direct Download (.exe):** [PHOENIX_Setup.exe](https://github.com/swayamprabhu2005/P.H.O.E.N.I.X./releases/latest/download/PHOENIX_Setup.exe)

---

## Overview

**P.H.O.E.N.I.X.** is an ultra-lightweight, 100% offline Windows desktop AI assistant inspired by futuristic holographic HUDs. It renders an interactive 3D **Dyson Sphere Core** floating directly on your desktop wallpaper or over any open application in a borderless, transparent window.

Designed specifically for **low-resource Windows computers (4 GB RAM, CPU-only, integrated graphics)** with an active memory footprint of only **~70–120 MB**.

---

## Key Features

1. **Procedural 3D Dyson Sphere (v3.0):**
   - **20 multi-axis interlocking toroids** rotating simultaneously on X, Y, and Z axes.
   - Compacted geometry with zero canvas edge clipping across all 3D rotations.
   - 3,200 dynamic holographic particle embers swirling in spherical orbits.
   - Smooth **top-to-bottom Ultron Blue wave transition** when entering sleep mode.
   - 100% transparent borderless overlay that can be dragged anywhere across the desktop.

2. **100% Offline Speech Recognition (Vosk):**
   - Uses `vosk-model-small-en-us-0.15` stored **directly inside the project folder (`models/`)**.
   - Zero internet connectivity required. Zero telemetry or audio streaming.
   - Microphone hardware is active **only** when awakened, and immediately halts when entering standby.

3. **Strict Silent Ambient Speech Filtering:**
   - Filters recognized speech strictly against registered commands.
   - Ambient conversation and background room noise are silently ignored without disruptive failure audios or popups.

4. **Personalized Assistant Persona (SAPI5):**
   - Greets user personalized on startup and on wake: *"At your service, Swayam."*
   - Change name anytime via voice (*"Call me [Name]"* or *"Change my name to [Name]"*).

5. **Specialized Application Modes:**
   - *"Learning mode Perplexity"* &rarr; Launches **Comet Browser** directly to Perplexity AI.
   - *"Coding mode VS Code"* &rarr; Launches Visual Studio Code.
   - *"Coding mode Antigravity"* &rarr; Launches Antigravity Agentic IDE.
   - *"Open Command Prompt"* / *"Open PowerShell"* &rarr; Launches CLI terminals.

6. **Google Services & Multi-Account Switching:**
   - *"Open Email"* / *"Open Gmail"* &rarr; Opens Gmail.
   - *"Open Google Drive"* &rarr; Opens Google Drive.
   - *"Switch to account 1"* up to *"Switch to account 5"* &rarr; Direct deep-link to `/u/{N-1}/` profiles.
   - *"Switch account"* &rarr; Opens Google Account Chooser.

7. **Voice File Navigation & Management:**
   - *"Open PDF [name]"* &rarr; Finds and opens matching `.pdf` file in active directory.
   - *"Open Word [name]"* &rarr; Finds and opens matching `.docx` document in active directory.
   - *"Open Text [name]"* &rarr; Finds and opens matching `.txt` file in active directory.
   - *"Open Presentation [name]"* &rarr; Finds and opens matching `.pptx` presentation in active directory.
   - *"Create folder [name]"*, *"Create text file [name]"*, *"Create word file [name]"*.
   - Stateful navigation: *"Go to D drive"*, *"Open folder [name]"*, *"Go back"*.

8. **Instant Desktop Control:**
   - *"Take screenshot"* &rarr; Captures screen directly to **`Downloads/`** + copies to clipboard.
   - *"Activate Snipping Tool"* &rarr; Launches Windows Snipping Tool.
   - *"Show desktop"* (`Win+D`), *"Open clipboard"* (`Win+V`), *"Lock PC"* (`Win+L`).
   - *"Volume up"*, *"Volume down"*, *"Mute"*, *"What time is it"*, *"Check battery"*.

---

## Quick Installation for End Users

1. Download the latest installer: **[PHOENIX_Setup.exe](https://github.com/swayamprabhu2005/P.H.O.E.N.I.X./releases/latest/download/PHOENIX_Setup.exe)**.
2. Double-click the installer and follow the setup wizard.
   > *Note for Windows users: If Microsoft Defender SmartScreen appears, click **"More info"** &rarr; **"Run anyway"**.*
3. Launch P.H.O.E.N.I.X. from your Desktop or Start Menu.
4. Click the floating 3D core to awaken and speak your command!

---

## Developer / Source Setup (Zero-Config First Run)

If you prefer cloning and running from source:

```bash
git clone https://github.com/swayamprabhu2005/P.H.O.E.N.I.X..git
cd P.H.O.E.N.I.X.
run.bat
```

> **Automatic Model Setup:** On first launch, `run.bat` automatically verifies the local environment, downloads the small Vosk acoustic model into `models/`, and boots the application. Zero manual configuration required.

### Dynamic Feature Addition
To add custom voice commands or actions without touching Python code:
```bash
add_feature.bat
```

---

## Technical Specifications

| Parameter | Specification |
| :--- | :--- |
| **Target OS** | Windows 10 / Windows 11 (64-bit) |
| **Minimum Hardware** | 4 GB RAM, Dual-Core 2.0 GHz CPU, Integrated GPU |
| **Active Memory Usage** | ~70 MB idle / ~120 MB peak active |
| **Speech Recognizer** | Vosk HMM-DNN acoustic model (offline, local) |
| **Voice Synthesis** | Microsoft SAPI5 Speech API (offline, native) |
| **Visual Runtime** | Microsoft Edge WebView2 (DirectX hardware accelerated WebGL) |

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
