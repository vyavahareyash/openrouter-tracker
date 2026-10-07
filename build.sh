#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

INSTALL_MODE=false
RUN_TESTS=false
for arg in "$@"; do
    if [[ "$arg" == "--install" ]]; then
        INSTALL_MODE=true
    fi
    if [[ "$arg" == "--test" ]]; then
        RUN_TESTS=true
    fi
done

if [ "$RUN_TESTS" = true ]; then
    echo "🧪 Running unit tests before build..."
    bash scripts/run_tests.sh
fi

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

# Copy AppIcon into bundle resources
mkdir -p "$APP_DST/Contents/Resources"
if [ -f "OpenRouterTrackerApp/AppIcon.icns" ]; then
    cp "OpenRouterTrackerApp/AppIcon.icns" "$APP_DST/Contents/Resources/AppIcon.icns"
fi

echo "✍️  [3/6] Signing app and widget extension..."
codesign --force --sign - --entitlements OpenRouterWidgetExtension/OpenRouterWidget.entitlements "$APP_DST/Contents/PlugIns/OpenRouterWidgetExtension.appex"
codesign --force --sign - --entitlements OpenRouterTrackerApp/OpenRouterTracker.entitlements "$APP_DST"

echo "💿 [4/6] Creating customized shareable DMG installer..."
bash scripts/create_dmg.sh "$APP_DST" "build/OpenRouterTracker.dmg" "OpenRouter Tracker"

echo "📦 [5/6] Creating shareable PKG & ZIP installers..."
rm -rf build/pkg_root build/OpenRouterTracker.pkg build/OpenRouterTracker.zip
mkdir -p build/pkg_root
cp -R "$APP_DST" build/pkg_root/
pkgbuild --root build/pkg_root --identifier com.openrouter.tracker --version 1.0 --install-location /Applications build/OpenRouterTracker.pkg > /dev/null 2>&1
rm -rf build/pkg_root
ditto -c -k --keepParent "$APP_DST" build/OpenRouterTracker.zip


if [ "$INSTALL_MODE" = true ]; then
    echo "🚀 [6/6] Installing to /Applications and enabling widget..."
    pkill -f OpenRouterTracker 2>/dev/null || true
    rm -rf /Applications/OpenRouterTracker.app
    cp -R "$APP_DST" /Applications/
    pluginkit -a /Applications/OpenRouterTracker.app/Contents/PlugIns/OpenRouterWidgetExtension.appex
    pluginkit -e use -i com.openrouter.tracker.widget
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f -R -trusted /Applications/OpenRouterTracker.app
    killall NotificationCenter chronod 2>/dev/null || true
    echo "✅ Successfully installed with custom app icon and refreshed daemons!"
else
    echo "🚀 [6/6] Registering build with macOS LaunchServices..."
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f -R -trusted "$APP_DST"
fi

echo ""
echo "✨ Build Complete!"
echo "Shareable Installers with Custom App Icon:"
echo "  - DMG: $(pwd)/build/OpenRouterTracker.dmg"
echo "  - PKG: $(pwd)/build/OpenRouterTracker.pkg"
echo "  - ZIP: $(pwd)/build/OpenRouterTracker.zip"
