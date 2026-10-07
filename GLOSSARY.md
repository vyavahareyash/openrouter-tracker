# Domain Glossary

Ubiquitous language and domain concepts for the OpenRouter Desktop Tracker and Widget.

### Core Domain Concepts

- **API Key (`apiKey`)**: Secret authentication credential for OpenRouter (`sk-or-v1-...`). Ephemeral in network requests; stored securely in container storage.
- **Tracked Key (`TrackedKey`)**: Metadata record representing an API key configured in the app, including `customLabel`, `isWidgetKey`, and masked display string.
- **Active Widget Key (`widgetKey`)**: The designated `TrackedKey` whose telemetry is displayed on the desktop widget. Exactly one key holds this role at any time.
- **Credits (`totalCredits`)**: Total credit balance purchased on the OpenRouter account, retrieved via `https://openrouter.ai/api/v1/credits`.
- **Usage (`keyUsage`, `totalUsage`)**: Consumption in USD. `keyUsage` reflects spending against a specific key; `totalUsage` reflects total account spending.
- **Key Limit (`keyLimit`)**: Optional credit limit configured on an API key.
- **Key Remaining (`keyRemaining`)**: Calculated balance remaining under a key's limit (`keyLimit - keyUsage`).
- **Periodic Breakdown (`usageDaily`, `usageWeekly`, `usageMonthly`)**: Velocity metrics showing spending over standard time intervals.
- **Free Tier (`isFreeTier`)**: State flag when an account has \$0 credits, zero usage limit, and relies on free model allocations.

### Architecture & System Concepts

- **Host App (`OpenRouterTrackerApp`)**: Companion macOS SwiftUI application managing credentials, multi-key configuration, and status inspection.
- **Widget Extension (`OpenRouterWidgetExtension`)**: Native macOS WidgetKit extension hosted by macOS system daemon (`chronod`).
- **Container Storage (`SharedStorage`)**: Filesystem-level shared persistence rooted in `~/Library/Containers/com.openrouter.tracker.widget/Data` enabling cross-process state access between App and Extension.
- **Timeline Entry (`OpenRouterEntry`)**: Temporal snapshot supplied to WidgetKit's `TimelineProvider` rendering the widget interface.
- **Refresh Intent (`RefreshBalanceIntent`)**: Interactive `AppIntent` triggered by widget button tap, executing `OpenRouterService.refreshWidgetKey()` and calling `reloadAllTimelines()`.
- **Ephemeral Session**: Stateless `URLSession` configuration preventing disk caching of auth headers and sensitive JSON payloads.
