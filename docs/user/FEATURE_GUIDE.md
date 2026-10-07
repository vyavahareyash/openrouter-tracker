# User Feature Guide

A complete guide to the features and capabilities of **OpenRouter Tracker**.

---

## 1. Companion Host App

The macOS companion app provides key management and high-fidelity metrics visualization:

- **Sidebar Key Management**: View all saved OpenRouter API keys with active nicknames and status badges.
- **Add Key Flow**: Securely add keys either manually or by importing from a local `.env` file (`OPENROUTER_API_KEY`).
- **Active Key Designation**: Set any tracked key as the primary key displayed on your Desktop Widget with one click.
- **Key Nicknames**: Rename keys anytime (e.g., "Personal Project", "Work Team Org", "Staging Agent") to stay organized.
- **Spend & Balance Gauges**:
  - **Account Balance**: Real-time remaining balance fetched from `/api/v1/credits`.
  - **Key Usage & Limit**: Direct credit consumption against the key's explicit limit (`usage / limit`).
  - **Usage Progress Bar**: Visual gauge reflecting credit burn percentage.
  - **Rate Limit Indicators**: Requests per minute / second quotas tied to your OpenRouter tier.

---

## 2. macOS Desktop Widgets

OpenRouter Tracker ships two native desktop widget sizes for macOS 14 Sonoma+:

### `systemSmall` (Compact Glance)
- **Top Row**: OpenRouter logo, key nickname, and active status beacon.
- **Center**: Prominent total balance display (`$XX.XX Remaining`).
- **Bottom**: Compact usage counter (`$X.XX used`) alongside an interactive `🔄` refresh button.

### `systemMedium` (Comprehensive Metrics)
- **Left Column**: High-visibility balance card with remaining credits and account status.
- **Right Column**: Detailed breakdown:
  - Key usage vs. hard limit (`$X.XX / $XX.XX`).
  - Visual burn bar showing percentage of credit allowance consumed.
  - Rate limit allowances (RPM / Requests per sec).
  - Last updated timestamp and interactive `🔄 Refresh` button.

---

## 3. Interactive 1-Click Refresh

Traditional widgets are passive and only refresh on system-determined timelines. OpenRouter Tracker integrates with Apple's **App Intents** framework:
- Clicking the `🔄` button directly on the desktop widget immediately invokes `RefreshBalanceIntent`.
- The system executes the background network refresh without launching the main application window or popping up docks.
- Updated metrics are instantly written to `SharedStorage` and the widget view refreshes in place within ~500ms.

---

## 4. Multi-Key Support

Manage separate keys for different clients, internal departments, or personal side-projects:
- Each key maintains its own isolated payload in the App Group container.
- Switching the active desktop widget key from the Companion App immediately updates the widget timeline.
- Deleting a key removes it from both the App Group storage and Apple Keychain.
