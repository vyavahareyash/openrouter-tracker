# ADR 0003: Windows Companion Application and Desktop Widget Architecture

## Context
OpenRouter Tracker was originally engineered exclusively for macOS using Swift, SwiftUI, and WidgetKit (`chronod`).
Windows does not have an identical desktop-pinned WidgetKit framework (Windows 11 only features an off-screen Widgets Board flyout). Additionally, developers on Windows need a first-class companion application, an always-accessible desktop widget with interactive 1-click refresh, and secure local credential storage comparable to Apple Keychain.

## Decision
Implement native Windows support using Python 3, PySide6 (Qt 6), and `pywin32`:

1. **Framework Choice**: PySide6 (Qt 6) provides:
   - High-performance, anti-aliased native graphics via `QPainter`.
   - Frameless translucent desktop windows for the desktop widget.
   - Cross-version Windows compatibility (Windows 10 and 11).
   - First-class system tray integration (`QSystemTrayIcon`).
   - Self-contained packaging into a single `.exe` via PyInstaller.
2. **Security & Cryptography**: API keys are encrypted at rest using **Windows DPAPI** (`win32crypt.CryptProtectData` / `CryptUnprotectData`), tied to the Windows user credential store, matching macOS Keychain security (`kSecClassGenericPassword`).
3. **Storage & State**: Data is persisted in `%APPDATA%\OpenRouterTracker\` as atomic JSON payloads (`keys_meta.json`, `openrouter_payload.json`, `payload_<id>.json`), maintaining architectural parity with `SharedStorage.swift`.
4. **Widget Interaction**: The desktop widget provides:
   - Dual size modes (`Small` radial ring gauge and `Medium` dual-column metrics).
   - Draggable placement with coordinate persistence.
   - An interactive tactile 1-click refresh button `🔄`.
   - Right-click desktop pinning and context actions.

## Consequences
- **Positive**: Complete feature parity between macOS and Windows.
- **Positive**: No external runtimes (like heavy .NET SDKs or web browser engines) required.
- **Positive**: 0% idle CPU and minimal RAM footprint.
- **Positive**: Standalone portable `.exe` distribution possible with PyInstaller.
