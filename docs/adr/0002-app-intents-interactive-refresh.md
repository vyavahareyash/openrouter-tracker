# ADR 0002: AppIntents Interactive Widget Refresh Without Background Daemons

## Context
Desktop widgets often require periodic data updates. Conventional desktop metric utilities run persistent background daemon processes or cron scripts to poll remote APIs. This consumes CPU cycles, drains laptop battery, and complicates lifecycle management when the user closes the application.

## Decision
Use Apple's `AppIntents` framework (`RefreshBalanceIntent`) paired with WidgetKit's interactive button capabilities (macOS 14 Sonoma+).

1. **Zero Continuous Background Work**: No launch agents, background timers, or persistent daemons are run.
2. **Interactive Button Trigger**: The widget renders a refresh button bound to `RefreshBalanceIntent()`.
3. **Execution Pipeline**:
   - User clicks `🔄 Refresh` button on desktop.
   - macOS triggers `RefreshBalanceIntent.perform()`.
   - `OpenRouterService.refreshWidgetKey()` fetches key metrics and credit data via ephemeral `URLSession`.
   - `SharedStorage.savePayload()` updates disk cache.
   - `WidgetCenter.shared.reloadAllTimelines()` invalidates the timeline and forces immediate UI repaint.

## Consequences
- **Positive**: 0% idle CPU and RAM footprint when not refreshing.
- **Positive**: Explicit user-controlled rate limiting prevents exceeding OpenRouter API rate quotas.
- **Negative**: Requires macOS 14.0+ (Sonoma or later) for interactive widget intent support.
