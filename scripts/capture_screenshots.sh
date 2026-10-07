#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

OUTPUT_DIR="${1:-$ROOT_DIR/screenshots}"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$ROOT_DIR/build/ModuleCache"

echo "📸 Compiling & capturing widget screenshots to $OUTPUT_DIR..."

swiftc -parse-as-library \
  -module-cache-path "$ROOT_DIR/build/ModuleCache" \
  Shared/OpenRouterModel.swift \
  Shared/KeychainHelper.swift \
  Shared/SharedStorage.swift \
  Shared/OpenRouterService.swift \
  OpenRouterWidgetExtension/RefreshBalanceIntent.swift \
  OpenRouterWidgetExtension/OpenRouterWidget.swift \
  OpenRouterWidgetExtension/OpenRouterWidgetView.swift \
  scripts/capture_widget_screenshots.swift \
  -o "$ROOT_DIR/build/capture_screenshots_bin"

"$ROOT_DIR/build/capture_screenshots_bin" "$OUTPUT_DIR"
