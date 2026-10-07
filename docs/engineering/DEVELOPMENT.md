# Developer & Build Guide

---

## 1. Prerequisites

- macOS 14 Sonoma or later
- Xcode 15+ (with Command Line Tools installed)
- Swift 5.9+

---

## 2. Local Setup & Building

### Command-Line Build
Compile both the host application and widget extension, sign them with ad-hoc certificates, and register them with macOS:

```bash
# Clean build and create application bundle
./build.sh
```

The output bundle will be placed at `build/OpenRouterTracker.app`.

### Opening in Xcode
```bash
open OpenRouterTracker.xcodeproj
```

---

## 3. Running Unit Tests

Run test suites using the project script or `xcodebuild`:

```bash
# Run via test runner script
./scripts/run_tests.sh

# Or directly via xcodebuild
xcodebuild test \
  -project OpenRouterTracker.xcodeproj \
  -scheme OpenRouterTracker \
  -destination 'platform=macOS'
```

---

## 4. Packaging Release DMG

Generate a customized, branded Apple disk image with custom Finder layout:

```bash
./scripts/create_dmg.sh build/OpenRouterTracker.app build/OpenRouterTracker.dmg "OpenRouter Tracker"
```

---

## 5. Code Formatting & Linting

OpenRouter Tracker uses Apple's native `swift-format`:

```bash
# Lint code against .swift-format rules
swift format lint --configuration .swift-format -r Shared OpenRouterTrackerApp OpenRouterWidgetExtension Tests

# Automatically format Swift files in place
swift format format -i --configuration .swift-format -r Shared OpenRouterTrackerApp OpenRouterWidgetExtension Tests
```

---

## 6. Git Pre-Commit & Pre-Push Hooks

Install local repository hooks:

```bash
./scripts/setup_hooks.sh
```

Pre-commit runs automatically on every `git commit`:
1. **Secret Scanning**: Verifies no raw production OpenRouter API keys (`sk-or-v1-...`) or private keys are staged.
2. **Swift Lint**: Validates staged Swift files against `.swift-format`.
3. **Script Verification**: Compiles Python generator scripts with `py_compile`.
4. **Fast Unit Tests**: Executes unit test suite (`./scripts/run_tests.sh`, ~40ms).

---

## 7. Capturing Automated Screenshots

Generate high-resolution dark and light mode screenshots for the repository showcase:

```bash
./scripts/capture_screenshots.sh
```
Screenshots are placed in the `screenshots/` directory.
