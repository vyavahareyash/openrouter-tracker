# Privacy Policy

**Last Updated:** October 2026

OpenRouter Tracker is designed with a strict **Local-First & Zero-Telemetry** architecture. We believe your API keys and usage metrics belong solely to you.

---

## 1. Zero External Telemetry

- **No Analytics**: OpenRouter Tracker contains zero third-party SDKs, tracking pixels, or diagnostic telemetry (no Google Analytics, Sentry, Mixpanel, or Firebase).
- **No Intermediary Servers**: The app and desktop widget never route traffic through any third-party server or developer-controlled proxy. All network traffic originates directly from your local machine and terminates exclusively at the official OpenRouter API endpoints (`https://openrouter.ai/api/v1/*`).

---

## 2. API Key Storage & Security

- **Apple Keychain**: API keys are securely stored using Apple's native Keychain Services API (`kSecClassGenericPassword`), protected by macOS hardware-backed encryption.
- **Sandboxed App Group Storage**: To enable the native macOS Desktop Widget to render balance metrics without spawning a continuous daemon process, decrypted API keys and response payloads are shared strictly across the sandboxed App Group container (`group.com.openrouter.tracker`).
- **Memory & Persistence**: Keys are never written to unencrypted log files, system crash logs, or temporary directories outside the sandboxed container.

---

## 3. Network Communication

OpenRouter Tracker makes outbound HTTPS requests exclusively to:
1. `https://openrouter.ai/api/v1/auth/key` — Fetches key label, credit limit, usage, and rate limits.
2. `https://openrouter.ai/api/v1/credits` — Fetches total account balance and remaining credits.

Requests include only the mandatory `Authorization: Bearer <API_KEY>` header. No device identifiers, IP geolocation, hardware specs, or personal identity markers are attached.

---

## 4. Background Execution & Resource Usage

- OpenRouter Tracker runs **zero persistent background daemons or cron jobs**.
- Widget scheduling and refresh cycles are handled exclusively by Apple's system-managed daemon (`chronod`), ensuring optimal battery efficiency and complete isolation when idle.

---

## 5. Contact & Auditing

The full source code for OpenRouter Tracker is open-source under the MIT License. You are encouraged to inspect network calls and Keychain implementations in `Shared/OpenRouterService.swift` and `Shared/KeychainHelper.swift`.
