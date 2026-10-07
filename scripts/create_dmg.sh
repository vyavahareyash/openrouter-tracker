#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

APP_PATH="${1:-$ROOT_DIR/build/OpenRouterTracker.app}"
DMG_OUTPUT="${2:-$ROOT_DIR/build/OpenRouterTracker.dmg}"
VOL_NAME="${3:-OpenRouter Tracker}"
APP_NAME="$(basename "$APP_PATH")"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: App bundle not found at $APP_PATH"
    exit 1
fi

echo "🎨 [1/5] Generating retina background asset..."
mkdir -p "$ROOT_DIR/build/ModuleCache"
swiftc -module-cache-path "$ROOT_DIR/build/ModuleCache" \
       "$ROOT_DIR/scripts/generate_dmg_background.swift" \
       -o "$ROOT_DIR/build/gen_dmg_bg"

BG_IMAGE="$ROOT_DIR/build/dmg_background.png"
"$ROOT_DIR/build/gen_dmg_bg" "$BG_IMAGE"

TEMP_DMG="$ROOT_DIR/build/temp_uncompressed.dmg"
rm -f "$TEMP_DMG" "$DMG_OUTPUT"

echo "💿 [2/5] Creating writable temporary disk image..."
hdiutil create -size 50m -fs HFS+ -volname "$VOL_NAME" -ov "$TEMP_DMG" > /dev/null

echo "📂 [3/5] Mounting volume & copying assets..."
ATTACH_INFO=$(hdiutil attach -readwrite -nobrowse -noverify -noautoopen "$TEMP_DMG")
MOUNT_DEV=$(echo "$ATTACH_INFO" | awk 'NR==1{print $1}')
MOUNT_DIR=$(echo "$ATTACH_INFO" | grep -o '/Volumes/.*' | head -n 1)

cleanup() {
    if [ -n "$MOUNT_DIR" ] && [ -d "$MOUNT_DIR" ]; then
        hdiutil detach "$MOUNT_DIR" -force > /dev/null 2>&1 || true
    fi
    rm -f "$TEMP_DMG"
}
trap cleanup EXIT

# Copy app & symlink Applications
cp -R "$APP_PATH" "$MOUNT_DIR/"
ln -s /Applications "$MOUNT_DIR/Applications"

# Copy background image
mkdir -p "$MOUNT_DIR/.background"
cp "$BG_IMAGE" "$MOUNT_DIR/.background/background.png"

# Setup volume icon
if [ -f "$ROOT_DIR/OpenRouterTrackerApp/AppIcon.icns" ]; then
    cp "$ROOT_DIR/OpenRouterTrackerApp/AppIcon.icns" "$MOUNT_DIR/.VolumeIcon.icns"
    if command -v SetFile &> /dev/null; then
        SetFile -a C "$MOUNT_DIR" || true
        SetFile -a V "$MOUNT_DIR/.VolumeIcon.icns" || true
        SetFile -a V "$MOUNT_DIR/.background" || true
    fi
fi

echo "🪄 [4/5] Customizing Finder window layout via AppleScript..."
osascript <<EOF || true
tell application "Finder"
    tell disk "$VOL_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {200, 150, 860, 570}
        
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 128
        set text size of theViewOptions to 13
        set background picture of theViewOptions to file ".background:background.png"
        
        -- Center positions for 660x420 window
        set position of item "$APP_NAME" of container window to {180, 210}
        set position of item "Applications" of container window to {480, 210}
        
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
EOF

sync
sleep 1

echo "🔒 [5/5] Detaching and compressing into final DMG..."
hdiutil detach "$MOUNT_DEV" -force > /dev/null || hdiutil detach "$MOUNT_DIR" -force > /dev/null
MOUNT_DIR="" # Prevent trap from trying to detach again

hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -ov -o "$DMG_OUTPUT" > /dev/null
rm -f "$TEMP_DMG"

echo "✅ Customized DMG created at: $DMG_OUTPUT"
