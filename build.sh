#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 [1/6] Generating Xcode project..."
python3 generate_project.py

echo "📦 [2/6] Compiling with xcodebuild..."
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

echo "✍️  [3/6] Signing app and widget extension..."
codesign --force --sign - --entitlements OpenRouterWidgetExtension/OpenRouterWidget.entitlements "$APP_DST/Contents/PlugIns/OpenRouterWidgetExtension.appex"
codesign --force --sign - --entitlements OpenRouterTrackerApp/OpenRouterTracker.entitlements "$APP_DST"

echo "🚀 [4/6] Registering with macOS LaunchServices..."
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f -R "$APP_DST"

echo "💿 [5/6] Creating shareable DMG installer..."
rm -rf build/dmg_staging build/OpenRouterTracker.dmg
mkdir -p build/dmg_staging
cp -R "$APP_DST" build/dmg_staging/
ln -s /Applications build/dmg_staging/Applications
hdiutil create -volname "OpenRouter Tracker" -srcfolder build/dmg_staging -ov -format UDZO build/OpenRouterTracker.dmg > /dev/null
rm -rf build/dmg_staging

echo "📦 [6/6] Creating shareable PKG installer..."
rm -rf build/pkg_root build/OpenRouterTracker.pkg
mkdir -p build/pkg_root
cp -R "$APP_DST" build/pkg_root/
pkgbuild --root build/pkg_root --identifier com.openrouter.tracker --version 1.0 --install-location /Applications build/OpenRouterTracker.pkg > /dev/null 2>&1
rm -rf build/pkg_root

echo "✨ All Done!"
echo "Shareable Installers:"
echo "  - DMG: $(pwd)/build/OpenRouterTracker.dmg"
echo "  - PKG: $(pwd)/build/OpenRouterTracker.pkg"
echo "  - ZIP: $(pwd)/build/OpenRouterTracker.zip"
