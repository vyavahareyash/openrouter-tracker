#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

OUTPUT_DIR="${1:-$ROOT_DIR/screenshots}"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ROOT_DIR/build/ModuleCache"

DEVELOPER_DIR="$(xcode-select -p)"
MACRO_PLUGIN="$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/usr/lib/swift/host/plugins/libSwiftUIMacros.dylib"

echo "📸 Compiling & capturing widget screenshots to $OUTPUT_DIR..."

swiftc -parse-as-library \
  -module-cache-path "$ROOT_DIR/build/ModuleCache" \
  Shared/OpenRouterModel.swift \
  Shared/KeychainHelper.swift \
  Shared/SharedStorage.swift \
  Shared/OpenRouterService.swift \
  Shared/MockData.swift \
  OpenRouterWidgetExtension/RefreshBalanceIntent.swift \
  OpenRouterWidgetExtension/OpenRouterWidget.swift \
  OpenRouterWidgetExtension/OpenRouterWidgetView.swift \
  scripts/capture_widget_screenshots.swift \
  -o "$ROOT_DIR/build/capture_widget_screenshots_bin"

"$ROOT_DIR/build/capture_widget_screenshots_bin" "$OUTPUT_DIR"

echo "🖥️ Compiling & capturing app screenshots to $OUTPUT_DIR..."

PLUGIN_ARGS=()
if [ -f "$MACRO_PLUGIN" ]; then
  PLUGIN_ARGS+=(-load-plugin-library "$MACRO_PLUGIN")
fi

swiftc -parse-as-library \
  -module-cache-path "$ROOT_DIR/build/ModuleCache" \
  "${PLUGIN_ARGS[@]}" \
  Shared/OpenRouterModel.swift \
  Shared/KeychainHelper.swift \
  Shared/SharedStorage.swift \
  Shared/OpenRouterService.swift \
  Shared/MockData.swift \
  OpenRouterTrackerApp/ContentView.swift \
  scripts/capture_app_screenshots.swift \
  -o "$ROOT_DIR/build/capture_app_screenshots_bin"

"$ROOT_DIR/build/capture_app_screenshots_bin" "$OUTPUT_DIR"

echo "✨ All screenshots generated in $OUTPUT_DIR"
