# System Architecture & Technical Specifications

This document defines the system architecture, inter-process communication (IPC) model, concurrency guarantees, and deep module boundaries of **OpenRouter Tracker**.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    subgraph Host Application ["Host App (OpenRouterTrackerApp)"]
        UI["ContentView (SwiftUI)"]
        Keychain["KeychainHelper (Security)"]
    end

    subgraph Shared IPC Container ["App Group Container (group.com.openrouter.tracker)"]
        KeysFile["keys.json (Multi-Key Storage)"]
        PayloadFile["balance.json (WidgetPayload Cache)"]
    end

    subgraph Widget Extension ["macOS Desktop Widget Extension"]
        Provider["OpenRouterWidget (TimelineProvider)"]
        WidgetUI["OpenRouterWidgetView (Small & Medium)"]
        Intent["RefreshBalanceIntent (AppIntents)"]
    end

    subgraph External ["External Services"]
        OR_API["OpenRouter API (/auth/key & /credits)"]
    end

    UI -->|Stores Keys & Metadata| SharedStorage
    UI -->|Fetches Live Metrics| OpenRouterService
    SharedStorage --> KeysFile
    SharedStorage --> PayloadFile

    Intent -->|Direct In-Widget Refresh| OpenRouterService
    OpenRouterService -->|Ephemeral HTTPS Request| OR_API
    OpenRouterService -->|Atomically Writes Cache| SharedStorage

    Provider -->|Reads Cached Payload| SharedStorage
    Provider -->|Feeds Entry| WidgetUI
```

---

## 2. Core Modules & Seams

### `OpenRouterService` (Network & Parse Engine)
- **Role**: Coordinates concurrent asynchronous network requests to OpenRouter endpoints.
- **Methods**:
  - `fetchData(apiKey:customNickname:) async -> WidgetPayload`: Queries `/api/v1/auth/key` and `/api/v1/credits` via `async let`.
  - `refreshWidgetKey() async -> WidgetPayload`: Identifies the designated active desktop key from `SharedStorage`, performs network fetch, and saves new payload.
- **Safety**: Uses ephemeral `URLSessionConfiguration` to guarantee no authentication headers or keys are persisted in standard disk caches.

### `SharedStorage` (Cross-Process Storage)
- **Role**: Acts as the shared IPC layer between the un-sandboxed/sandboxed app and the widget extension.
- **Methods**:
  - `loadAllKeys() -> [TrackedKey]`
  - `saveKeys(_ keys: [TrackedKey])`
  - `getWidgetKey() -> TrackedKey?`
  - `setWidgetKey(id: UUID)`
  - `loadPayload() -> WidgetPayload?`
  - `savePayload(_ payload: WidgetPayload)`
- **Invariants**:
  - Write operations execute atomically to avoid partial JSON reads.
  - Exactly one tracked key possesses `isWidgetKey == true`.

### `RefreshBalanceIntent` (Interactive In-Widget Seam)
- **Role**: Conforms to Apple's `AppIntent` framework.
- **Execution Flow**:
  1. Triggered by user tapping the in-widget refresh button.
  2. Executes `OpenRouterService.refreshWidgetKey()` in a background worker context provided by macOS `chronod`.
  3. Signals `WidgetCenter.shared.reloadAllTimelines()`.
  4. Returns `.result()`, causing immediate view re-render without launching the companion app.
