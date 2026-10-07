<p align="center">
  <img src="assets/banner.png" alt="OpenRouter Tracker Banner" width="100%">
</p>

# OpenRouter Tracker

[![macOS](https://img.shields.io/badge/macOS-14_Sonoma+-000000?logo=apple&logoColor=white)](https://apple.com/macos)
[![Swift](https://img.shields.io/badge/Swift-5.9-F05138?logo=swift&logoColor=white)](https://swift.org)
[![Framework](https://img.shields.io/badge/UI-SwiftUI_%26_WidgetKit-0A84FF)](https://developer.apple.com/xcode/swiftui/)
[![Background](https://img.shields.io/badge/Daemon-Zero_Background_Tasks-success)](#zero-background-resource-usage)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_On--Device-7C3AED)](PRIVACY_POLICY.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Download-Latest_DMG-06B6D4?logo=apple)](https://github.com/vyavahareyash/openrouter-tracker/releases/latest)

OpenRouter Tracker is a native macOS desktop widget and companion app designed for developers, engineering teams, and autonomous AI agents. It gives you instant glanceability over your OpenRouter credit balances, usage pacing, and rate limits directly on your desktop—with **zero background battery drain** and an **interactive 1-click refresh button**.

---

## The "Blind Key" Problem

Developers frequently work with organization-provisioned OpenRouter API keys or separate project tokens without direct access to the web dashboard. You only discover a key has run out of credits when an active build pipeline, local coding agent, or evaluation run crashes mid-flight.

OpenRouter Tracker solves this by placing live, interactive balance gauges right on your macOS desktop:

```text
Glanceable Balance = Real-time Account Balance - Key Spend
```

- **Interactive 1-Click Refresh**: Tap the `🔄` button directly on the desktop widget to instantly query the latest balance in-place via Apple's native `AppIntents`.
- **Zero Background Resource Usage**: Runs **no** background scripts or daemon processes. Apple's system scheduler (`chronod`) manages timeline updates without battery overhead.
- **Hardware Keychain Encryption**: Keys are stored locally using Apple Keychain Services and shared across the sandboxed App Group container. Zero middleman servers or analytics.

---

## Downloads & Installation

### Option 1: Homebrew (Recommended)

Install directly via Homebrew (automatically bypasses browser Gatekeeper quarantine):

```bash
brew tap vyavahareyash/tap
brew install --cask openrouter-tracker
```

### Option 2: Direct Download (DMG)
Download the latest pre-compiled Apple disk image:
- 🍏 **macOS (Universal / Apple Silicon & Intel)**: [Download OpenRouterTracker.dmg](https://github.com/vyavahareyash/openrouter-tracker/releases/latest/download/OpenRouterTracker.dmg)

> 💡 **Gatekeeper First-Run Notice**: If downloaded through a web browser, macOS attaches quarantine attributes to unnotarized open-source binaries. If macOS blocks first launch, run:
> ```bash
> xattr -cr /Applications/OpenRouterTracker.app
> ```
> Or navigate to **System Settings > Privacy & Security** and click **Open Anyway**. Alternatively, download via terminal (`curl -LO https://github.com/vyavahareyash/openrouter-tracker/releases/latest/download/OpenRouterTracker.dmg`) or use Homebrew above to avoid this prompt entirely.

### Option 3: Build From Source
```bash
# Clone the repository
git clone https://github.com/vyavahareyash/openrouter-tracker.git
cd openrouter-tracker

# Clean build and bundle the app & widget
./build.sh

# Launch the app
open build/OpenRouterTracker.app
```

---

## Key Features

- ⚡ **1-Click Interactive Widget Refresh**: Powered by `AppIntents`. Click the refresh icon directly on the widget to update balances in < 500ms without opening the host application.
- 🔋 **Zero Battery Overhead**: Managed strictly by macOS `chronod`. No continuous daemon, timer loops, or menubar CPU hogs.
- 🖥️ **Multiple Widget Sizes**: Choose between `systemSmall` (compact balance beacon) and `systemMedium` (detailed credit limit burn bar and rate-limit counters).
- 🔑 **Multi-Key Management**: Add multiple project or client keys, label them with custom nicknames, and toggle which key appears on your desktop with one click.
- 🔐 **Defense-in-Depth Privacy**: Keys are encrypted via Apple Keychain (`kSecClassGenericPassword`) and cached in the sandboxed App Group container (`group.com.openrouter.tracker`).
- 📊 **Rate Limit Gauges**: View real-time requests-per-second and hourly rate limit allocations returned by OpenRouter's tier system.

---

## Visual Showcase

<table>
  <tr>
    <td align="center"><b>Small Widget (Light)</b></td>
    <td align="center"><b>Small Widget (Dark)</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/widget_small_light.png" alt="Small Widget Light" width="360"></td>
    <td><img src="screenshots/widget_small_dark.png" alt="Small Widget Dark" width="360"></td>
  </tr>
  <tr>
    <td align="center"><b>Medium Widget (Light)</b></td>
    <td align="center"><b>Medium Widget (Dark)</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/widget_medium_light.png" alt="Medium Widget Light" width="360"></td>
    <td><img src="screenshots/widget_medium_dark.png" alt="Medium Widget Dark" width="360"></td>
  </tr>
  <tr>
    <td align="center"><b>Companion App (Light)</b></td>
    <td align="center"><b>Companion App (Dark)</b></td>
  </tr>
  <tr>
    <td><img src="screenshots/app_light.png" alt="Companion App Light" width="360"></td>
    <td><img src="screenshots/app_dark.png" alt="Companion App Dark" width="360"></td>
  </tr>
</table>

> 📸 **Interactive Gallery**: View the full responsive screenshot comparison in the [Screenshot Gallery](screenshots/index.html).

---

## Adding the Widget to macOS Desktop

1. Open **OpenRouter Tracker** once and add your API key (`sk-or-v1-...`).
2. Right-click any open area on your macOS Desktop and select **"Edit Widgets..."**.
3. Search for **"OpenRouter"** in the widget gallery.
4. Drag either the **Small** or **Medium** widget onto your desktop or Notification Center.

---

## Documentation

Full architectural specifications, developer guides, and user manuals are organized in the [`docs/`](docs/INDEX.md) hub:

- [User Feature Guide](docs/user/FEATURE_GUIDE.md) — Walkthrough of all app capabilities, widget sizes, and multi-key workflows.
- [Onboarding & FAQ](docs/user/FAQ_AND_ONBOARDING.md) — 3-step setup guide, troubleshooting blank widgets, and FAQs.
- [Security & API Key Management](docs/user/SECURITY_AND_KEYS.md) — Keychain architecture, sandboxing, and token safety.
- [System Architecture](docs/engineering/ARCHITECTURE.md) — Module catalog, App Group IPC, AppIntents lifecycle, and Mermaid diagrams.
- [Calculations & Formulas](docs/engineering/CALCULATIONS.md) — Mathematical formulas for usage burn rate and depletion thresholds.
- [Developer Guide](docs/engineering/DEVELOPMENT.md) — CLI build scripts, testing with coverage, and packaging DMGs.
- [Product Specifications](docs/product/SPECIFICATION.md) — OpenRouter API schemas and offline resilience invariants.
- [Product Roadmap](docs/product/ROADMAP.md) — Upcoming features (Menu Bar status item, low balance alerts).
- [Architecture Decision Records (ADR)](docs/adr/) — Technical decisions behind App Group storage and AppIntents.

---

## Private by Default

OpenRouter Tracker makes **zero network calls** to any third-party analytics, tracking, or intermediary server. Outbound HTTPS traffic connects exclusively to official OpenRouter endpoints (`https://openrouter.ai/api/v1/*`). Review our formal [Privacy Policy](PRIVACY_POLICY.md).

---

## License

This project is licensed under the [MIT License](LICENSE).
