# Architecture & Deep Module Design

This document details the modules, interfaces, and seams governing the OpenRouter macOS Tracker and Widget.

```
┌────────────────────────────────────────────────────────┐
│ UI / Extension Tier: ContentView, OpenRouterWidget     │
└──────────┬─────────────────────────────────┬───────────┘
           │ (Internal Seam)                 │ (Internal Seam)
┌──────────▼───────────────┐     ┌───────────▼───────────┐
│ SharedStorage            │     │ OpenRouterService     │
│ [AppGroup + Container]   │     │ [API Client + Parser] │
└──────────────────────────┘     └───────────────────────┘
```

---

## 1. Module Catalog

### `OpenRouterService` (Shared Module)
- **Depth**: **High**. Complex networking, authentication headers, error classification, response parsing, and concurrency coordination hidden behind small public static methods.
- **Interface**:
  - `fetchData(apiKey:customNickname:) async -> WidgetPayload`: Fetches key metadata (`/api/v1/auth/key`) and credit balances (`/api/v1/credits`) concurrently.
  - `refreshWidgetKey() async -> WidgetPayload`: Loads active widget key, refreshes data, and persists to cache.
- **Invariants**:
  - Ephemeral `URLSession` used exclusively to prevent disk caching of API keys or auth headers.
  - Failures populate `errorMessage` in `WidgetPayload` rather than throwing uncaught exceptions to caller.

### `SharedStorage` (Persistence Module)
- **Depth**: **High**. Container path calculation, multi-key JSON serialization, legacy file migrations, and atomic writes encapsulated behind static helpers.
- **Interface**:
  - `loadAllKeys() -> [TrackedKey]`
  - `addKey(...) -> TrackedKey`
  - `deleteKey(id: UUID)`
  - `setWidgetKey(id: UUID)`
  - `getWidgetKey() -> TrackedKey?`
  - `loadPayload() -> WidgetPayload?`
  - `savePayload(_ payload: WidgetPayload)`
- **Invariants**:
  - Exactly one key can have `isWidgetKey == true` when keys exist.
  - Directory creation is idempotent via `withIntermediateDirectories: true`.

### `RefreshBalanceIntent` (Interactive Seam)
- **Role**: Adapter connecting WidgetKit button events to `OpenRouterService`.
- **Interface**: Standard AppIntent `perform() async throws -> some IntentResult`.
- **Behavior**: Calls `refreshWidgetKey()` then instructs `WidgetCenter.shared.reloadAllTimelines()`.

### `OpenRouterWidget` (WidgetKit Adapter)
- **Role**: Implements `TimelineProvider` for WidgetKit.
- **Behavior**:
  - `placeholder()`: Returns static placeholder entry.
  - `getSnapshot()`: Returns cached payload or fallback.
  - `getTimeline()`: Reads cached payload from `SharedStorage`, scheduling a periodic update policy while honoring interactive intent refreshes.

### `ContentView` (Host App UI)
- **Role**: Companion management UI.
- **Behavior**: Enables adding/editing/deleting keys, switching the active widget key, reading `.env` keys, and triggering manual refreshes.

---

## 2. Seams & Verification Surfaces

| Seam | Caller | Callee | Contract |
| :--- | :--- | :--- | :--- |
| **API Client Seam** | `ContentView`, `RefreshBalanceIntent` | `OpenRouterService` | Returns `WidgetPayload` (contains error or valid data; never crashes caller) |
| **Persistence Seam**| `OpenRouterWidget`, `ContentView` | `SharedStorage` | Thread-safe, container-isolated JSON file I/O |
| **Intent Action Seam**| Widget UI button | `RefreshBalanceIntent` | Asynchronous void return updating `WidgetCenter` |
