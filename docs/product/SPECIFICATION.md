# Product Specification & API Contracts

This specification defines the functional behaviors, API endpoints, schema contracts, and error resilience standards for **OpenRouter Tracker**.

---

## 1. Upstream API Specifications

OpenRouter Tracker communicates with two endpoints on `https://openrouter.ai/api/v1/`:

### Endpoint 1: Key Metadata & Usage
- **URL**: `GET https://openrouter.ai/api/v1/auth/key`
- **Headers**: `Authorization: Bearer <API_KEY>`
- **Expected Response (200 OK)**:
```json
{
  "data": {
    "label": "My Key Label",
    "usage": 14.85,
    "limit": 50.00,
    "is_free_tier": false,
    "rate_limit": {
      "requests": 500,
      "interval": "10s"
    }
  }
}
```

### Endpoint 2: Account Credits
- **URL**: `GET https://openrouter.ai/api/v1/credits`
- **Headers**: `Authorization: Bearer <API_KEY>`
- **Expected Response (200 OK)**:
```json
{
  "data": {
    "total_credits": 100.00,
    "total_usage": 45.20
  }
}
```

---

## 2. In-Memory and Persisted Schema: `WidgetPayload`

```swift
struct WidgetPayload: Codable {
    let keyId: UUID?
    let label: String
    let usage: Double
    let limit: Double?
    let isFreeTier: Bool
    let rateLimitRequests: Int?
    let rateLimitInterval: String?
    let totalCredits: Double
    let totalUsage: Double
    let lastUpdated: Date
    let errorMessage: String?
}
```

---

## 3. Resilience & Error Invariants

1. **Non-Blocking Failures**: Network failures, 401 unauthorized errors, or timeout exceptions must not crash or freeze the UI. An error banner is set inside the payload and the last successfully cached metrics remain visible.
2. **Offline Tolerance**: If a user is offline, the desktop widget displays previously cached values with an amber staleness indicator rather than an empty widget.
