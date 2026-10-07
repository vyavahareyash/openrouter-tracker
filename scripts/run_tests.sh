#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p "$ROOT_DIR/build/ModuleCache"
DEVELOPER_DIR="$(xcode-select -p)"

echo "🔨 Compiling test suite..."

swiftc -parse-as-library \
  -module-cache-path "$ROOT_DIR/build/ModuleCache" \
  -F "$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/Library/Frameworks" \
  -I "$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/usr/lib" \
  -L "$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/usr/lib" \
  -framework XCTest \
  -Xlinker -rpath -Xlinker "$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/Library/Frameworks" \
  -Xlinker -rpath -Xlinker "$DEVELOPER_DIR/Platforms/MacOSX.platform/Developer/usr/lib" \
  Shared/OpenRouterModel.swift \
  Shared/KeychainHelper.swift \
  Shared/SharedStorage.swift \
  Shared/OpenRouterService.swift \
  Shared/MockData.swift \
  Tests/OpenRouterTrackerTests.swift \
  -o "$ROOT_DIR/build/test_runner_bin"

echo "🚀 Executing test runner..."
"$ROOT_DIR/build/test_runner_bin"
