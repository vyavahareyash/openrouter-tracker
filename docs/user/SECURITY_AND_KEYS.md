# Security & API Key Management

---

## 1. Key Storage Hierarchy

OpenRouter Tracker implements a defense-in-depth model for API key safety on macOS:

```text
┌────────────────────────────────────────────────────────┐
│                   Apple Keychain                       │
│    (kSecClassGenericPassword, Hardware AES-256)        │
└───────────────────────────┬────────────────────────────┘
                            │ Decrypt for IPC
                            ▼
┌────────────────────────────────────────────────────────┐
│            App Group Sandboxed Container               │
│             (group.com.openrouter.tracker)             │
│   Shared between Host App & OpenRouterWidgetExtension  │
└────────────────────────────────────────────────────────┘
```

1. **Primary Persistence**: Keys are saved to the user's login Keychain under service identifier `com.openrouter.tracker`.
2. **IPC Container**: To allow the widget extension to refresh without requiring the host app window to open, keys and the cached response JSON are held in the sandboxed directory `~/Library/Group Containers/group.com.openrouter.tracker`.

---

## 2. API Key Permissions & Recommendations

- **No Write Permissions Required**: OpenRouter Tracker only makes read-only requests to `/api/v1/auth/key` and `/api/v1/credits`. It never creates new keys, modifies limits, or dispatches LLM model completions (`/api/v1/chat/completions`).
- **Org-Provided Keys**: If using keys provided by an organization or enterprise account, the tracker will safely display the credit limits set on that key without granting administrative access.
- **Key Rotation**: When you regenerate a key on OpenRouter, simply update the key in the companion app. The cached payload will immediately update upon refresh.
