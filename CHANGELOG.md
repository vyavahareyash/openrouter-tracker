# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.6] - 2026-10-08

### Added
- **Motion Graphics Banner**: Code-synthesized 18fps animated banner (`assets/banner.gif`) capturing 1-click interactive tactile refresh, 360° arrow spin, and real-time balance flash.
- **GitHub Social Preview**: Dedicated 1280×640 2:1 isometric hero thumbnail (`assets/thumbnail.png`) featuring 3D floating desktop widgets and feature pills.
- **Motion & Asset Scripts**: `scripts/generate_motion_banner.py` and `scripts/generate_github_thumbnail.py` for automated reproducible branding asset synthesis.

### Changed
- **Redesigned App Icon**: Modern circular instrument dial emblem with polished silver bezel, cyan-to-violet radial gauge arc, and slanted neural circuit API key across host app, widget extension, and `Assets.xcassets`.
- **README Header**: Switched header visual to motion graphics banner.

---

## [1.0.0] - 2026-10-07

### Added
- **Native macOS Desktop Widget**: Full support for macOS 14 Sonoma+ Desktop Widgets via WidgetKit (`systemSmall` and `systemMedium`).
- **Interactive 1-Click Refresh**: Direct in-widget refresh button powered by `AppIntents` and `chronod` scheduling without requiring a background app process.
- **Companion Host App**: Clean SwiftUI desktop app to track keys, inspect account balance, key limits, and rate-limit allocations.
- **Multi-Key Management**: Add, label, and switch between multiple OpenRouter API keys with independent caching and custom nicknames.
- **Visual Analytics**: Interactive spend metrics, usage bar indicators, and hourly rate-limit allowances.
- **App Group Shared Container**: Seamless cross-process persistence between the host app and widget extension (`group.com.openrouter.tracker`).
- **Apple Keychain Integration**: Secure on-device hardware-encrypted credential persistence.
- **Retina DMG Packager**: Automated `scripts/create_dmg.sh` with custom AppleScript layout and branded installer background.
- **Documentation Hub**: Comprehensive architectural specifications, developer guides, and user manuals under `docs/`.
