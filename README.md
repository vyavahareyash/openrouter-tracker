<p align="center">
  <img src="assets/banner.gif" alt="OpenRouter Tracker Banner" width="100%">
</p>

# OpenRouter Tracker

[![macOS](https://img.shields.io/badge/macOS-14_Sonoma+-000000?logo=apple&logoColor=white)](https://apple.com/macos)
[![Windows](https://img.shields.io/badge/Windows-10_%2F_11-0078D6?logo=windows&logoColor=white)](#windows)
[![Release](https://img.shields.io/badge/Download-Latest_Release-06B6D4)](https://github.com/vyavahareyash/openrouter-tracker/releases/latest)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_On--Device-7C3AED)](PRIVACY_POLICY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Sponsor](https://img.shields.io/badge/Sponsor-Buy%20Me%20a%20Coffee-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/vyavahareyash)

Native desktop widget and companion app to monitor OpenRouter credits, spend velocity, and rate limits in real time—with **zero idle battery drain** and **1-click instant refresh**.

> 💡 **The Problem**: Working with provisioned keys, CI pipelines, or local coding agents without dashboard access? Keys exhaust silently mid-run. OpenRouter Tracker places live, glanceable balance gauges directly on your desktop.

---

## ⚡ Quick Start

| Platform | Quick Install (Terminal) | Direct Download |
| :--- | :--- | :--- |
| 🍏 **macOS** *(14+ Sonoma)* | `brew tap vyavahareyash/tap`<br>`brew install --cask openrouter-tracker` | [OpenRouterTracker.dmg](https://github.com/vyavahareyash/openrouter-tracker/releases/latest/download/OpenRouterTracker.dmg) |
| 🪟 **Windows** *(10 / 11)* | `irm https://raw.githubusercontent.com/vyavahareyash/openrouter-tracker/main/scripts/install.ps1 \| iex` | [OpenRouterTracker.exe](https://github.com/vyavahareyash/openrouter-tracker/releases/latest/download/OpenRouterTracker.exe) · [ZIP](https://github.com/vyavahareyash/openrouter-tracker/releases/latest/download/OpenRouterTracker-windows-x64.zip) |

### 2-Step Setup
1. Launch the app and paste your OpenRouter key (`sk-or-v1-...`).
2. Add the widget:
   - **macOS**: Right-click Desktop → **Edit Widgets...** → Search **OpenRouter** → Drag Small or Medium widget.
   - **Windows**: Frameless desktop widget appears on launch; right-click for tray menu, resize, and pin options.

---

## 🖼️ Showcase

<p align="center">
  <img src="screenshots/widget_medium_light.png" alt="Medium Widget Light" width="48%">
  <img src="screenshots/widget_medium_dark.png" alt="Medium Widget Dark" width="48%">
</p>

> 📸 Explore all widget sizes, light/dark themes, and app views in the [Interactive Screenshot Gallery](screenshots/index.html).

---

## ✨ Features

- **1-Click Refresh**: Tap `🔄` on the widget to update balances in < 500ms via macOS `AppIntents` / Windows async threads.
- **Zero Idle Overhead**: No background daemon polling; updates handled by Apple `chronod` or Qt event loops.
- **Dual Widget Sizes**: Compact radial donut (**Small**) or multi-metric burn rate breakdown (**Medium**).
- **Multi-Key Vault**: Manage, test, and nickname multiple project/org keys; toggle active widget key in 1 click.
- **Hardware-Backed Encryption**: Secured via Apple Keychain Services (`kSecClassGenericPassword`) and Windows DPAPI (`CryptProtectData`). Zero third-party network traffic.

---

## 🛠️ Advanced & Troubleshooting

<details>
<summary><b>macOS Gatekeeper & Keychain Setup</b></summary>

- **Gatekeeper Bypass** (ad-hoc signed open-source build):
  ```bash
  xattr -cr /Applications/OpenRouterTracker.app
  ```
  *Or: Right-click app in Finder → Open → click Open.*
- **Keychain Prompt**: Select **"Always Allow"** and provide user password once so the widget can query keys securely without prompts.
</details>

<details>
<summary><b>Building from Source</b></summary>

**macOS**:
```bash
git clone https://github.com/vyavahareyash/openrouter-tracker.git
cd openrouter-tracker
./build.sh
open build/OpenRouterTracker.app
```

**Windows**:
```powershell
pip install -r windows/requirements.txt
.\run_windows.bat
# Or package standalone binary:
.\build_windows.bat
```
</details>

<details>
<summary><b>Headless / CLI Fallback (`scripts/check_usage.py`)</b></summary>

Lightweight zero-dependency CLI script for Linux/servers/headless setups:
```bash
python3 scripts/check_usage.py [YOUR_KEY]
```
*(Reads inline argument, `OPENROUTER_API_KEY` env var, or local `.env`).*
</details>

---

## 📚 Documentation & Reference

See the [`docs/`](docs/INDEX.md) hub for complete architecture and guides:

- [Feature Guide](docs/user/FEATURE_GUIDE.md) & [Onboarding FAQ](docs/user/FAQ_AND_ONBOARDING.md)
- [Security & Keychain Architecture](docs/user/SECURITY_AND_KEYS.md)
- [System Architecture](docs/engineering/ARCHITECTURE.md) & [Burn Rate Formulas](docs/engineering/CALCULATIONS.md)
- [Developer Guide](docs/engineering/DEVELOPMENT.md) & [Roadmap](docs/product/ROADMAP.md)

---

## 🔒 Privacy & License

- **100% Private**: Zero analytics or middleman servers. Only queries `https://openrouter.ai/api/v1/*`. Details in [PRIVACY_POLICY.md](PRIVACY_POLICY.md).
- **License**: [MIT](LICENSE) © Yash Vyavahare.

<p align="left">
  <a href="https://buymeacoffee.com/vyavahareyash" target="_blank">
    <img src="assets/bmc_official_button.png" alt="Buy Me A Coffee" height="42">
  </a>
</p>
