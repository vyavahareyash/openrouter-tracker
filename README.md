# OpenRouter macOS Desktop Widget

Native macOS Desktop Widget (macOS 14 Sonoma+) to track OpenRouter account balance, key usage, and credit limits with an interactive 1-click `🔄 Refresh` button.

## Features
- **Native macOS Widget**: Sits directly on your Mac desktop via the official **"Edit Widgets..."** gallery.
- **Zero Background Resource Usage**: macOS system daemon (`chronod`) renders and schedules the widget; no continuous scripts or processes required.
- **Interactive 1-Click Refresh**: Built with `AppIntents`; tap the 🔄 button directly on the desktop widget to fetch the latest balance in-place.
- **Multiple Sizes**: Supports `systemSmall` (compact balance & usage) and `systemMedium` (detailed account breakdown).
- **Host Companion App**: Simple configuration UI to view active metrics, load from `.env`, or update your key.

## Quick Start

### 1. Configure `.env`
```bash
cp .env.example .env
# Edit .env and paste your OpenRouter key:
# OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx...
```

### 2. Build & Register
Run the automated build script:
```bash
./build.sh
```

### 3. Add Widget to Desktop
1. Launch the app once to load your key:
   ```bash
   open build/OpenRouterTracker.app
   ```
2. Right-click any empty space on your macOS Desktop and select **"Edit Widgets..."**.
3. Search for **"OpenRouter"**.
4. Choose **Small** or **Medium** and drag it onto your desktop!

## Xcode Development
You can also open the project directly in Xcode:
```bash
open OpenRouterTracker.xcodeproj
```

## Documentation
- [Domain Glossary](GLOSSARY.md): Ubiquitous language, OpenRouter metrics, and system definitions.
- [Architecture & Deep Modules](docs/architecture.md): Module catalog, seams, interfaces, and invariants.
- [ADR 0001: Container-Based Shared Storage](docs/adr/0001-app-group-shared-storage.md): App ↔ Widget cross-process persistence design.
- [ADR 0002: AppIntents Interactive Refresh](docs/adr/0002-app-intents-interactive-refresh.md): Zero-daemon refresh mechanism.
- [Agent Guidelines](AGENTS.md): Local issue tracker conventions & skills layout.
