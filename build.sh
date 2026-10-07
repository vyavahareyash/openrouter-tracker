#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 [1/5] Generating Xcode project..."
python3 generate_project.py

echo "📦 [2/5] Compiling with xcodebuild..."
xcodebuild -project OpenRouterTracker.xcodeproj \
           -scheme OpenRouterTracker \
           -configuration Release \
           -derivedDataPath ./build/DerivedData \
           CODE_SIGNING_ALLOWED=NO \
           CODE_SIGNING_REQUIRED=NO \
           build > /dev/null

APP_SRC="./build/DerivedData/Build/Products/Release/OpenRouterTracker.app"
APP_DST="./build/OpenRouterTracker.app"

rm -rf "$APP_DST"
cp -R "$APP_SRC" "$APP_DST"

echo "✍️  [3/5] Signing app and widget extension..."
codesign --force --sign - --entitlements OpenRouterWidgetExtension/OpenRouterWidget.entitlements "$APP_DST/Contents/PlugIns/OpenRouterWidgetExtension.appex"
codesign --force --sign - --entitlements OpenRouterTrackerApp/OpenRouterTracker.entitlements "$APP_DST"

echo "🚀 [4/5] Registering with macOS LaunchServices..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f -R "$APP_DST"

echo "✨ [5/5] Success! Built at $APP_DST"
echo ""
echo "To install to /Applications, run:"
echo "  cp -R build/OpenRouterTracker.app /Applications/"
echo ""
echo "To add widget to desktop:"
echo "  1. Launch OpenRouterTracker once (open build/OpenRouterTracker.app)"
echo "  2. Right-click desktop -> 'Edit Widgets...'"
echo "  3. Search for 'OpenRouter' and drag it to your desktop!"
