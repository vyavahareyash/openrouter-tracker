# ADR 0001: Container-Based Shared Storage for App and Widget Extension

## Context
macOS sandboxes the Host App and the Widget Extension into separate process boundaries. The host app configures API keys and user settings, while the widget extension runs inside `chronod` and needs access to credentials and cached telemetry payloads without requiring the host app to be running.

Standard macOS App Groups require a paid Apple Developer Account provisioning profile. For development, local builds, and non-notarized distribution, an alternative cross-process storage mechanism was required.

## Decision
Implement `SharedStorage` as a deep persistence module targeting `~/Library/Containers/com.openrouter.tracker.widget/Data`.

1. **Storage Location**: The Widget container path is accessible to both the Widget process and the main app process on macOS.
2. **Persistence Schema**:
   - `keys_meta.json`: Serialized array of `TrackedKey` objects (labels, UUIDs, active widget key designation).
   - `openrouter_payload.json`: Cached `WidgetPayload` consumed synchronously by `OpenRouterTimelineProvider`.
   - `payload_<uuid>.json`: Key-specific cached metrics.
3. **Interface Simplicity**: Callers interact with simple static methods (`loadAllKeys()`, `savePayload()`, `getWidgetKey()`) without managing paths, file locks, or serialization errors.

## Consequences
- **Positive**: Zero external dependencies, works without paid Apple Developer certificates or provisioning entitlements.
- **Positive**: Widgets can render instantly from cache even during network partitions or offline states.
- **Negative**: If sandbox container permissions change across major macOS versions, `storageDirectory` path resolution must be maintained.
