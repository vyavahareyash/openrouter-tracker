import Foundation

public struct OpenRouterService {
    // Ephemeral URLSession: Zero disk caching of auth headers or responses
    private static var session: URLSession {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 15
        return URLSession(configuration: config)
    }

    public static func fetchData(apiKey: String, customNickname: String) async -> WidgetPayload {
        let cleanKey = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleanKey.isEmpty else {
            return WidgetPayload.empty
        }

        var payload = WidgetPayload(
            keyLabel: "Unknown",
            customNickname: customNickname,
            keyMasked: TrackedKey.mask(cleanKey),
            keyUsage: 0.0,
            keyLimit: nil,
            keyRemaining: nil,
            usageDaily: nil,
            usageWeekly: nil,
            usageMonthly: nil,
            totalCredits: 0.0,
            totalUsage: 0.0,
            totalBalance: 0.0,
            isFreeTier: false,
            lastUpdated: Date(),
            errorMessage: nil
        )

        // 1. Key Metrics & Limits
        do {
            guard let keyURL = URL(string: "https://openrouter.ai/api/v1/auth/key") else {
                throw URLError(.badURL)
            }
            var keyReq = URLRequest(url: keyURL)
            keyReq.setValue("Bearer \(cleanKey)", forHTTPHeaderField: "Authorization")
            keyReq.setValue("OpenRouterTracker/2.0", forHTTPHeaderField: "User-Agent")

            let (keyData, keyResp) = try await session.data(for: keyReq)
            if let httpResp = keyResp as? HTTPURLResponse, httpResp.statusCode != 200 {
                let msg = String(data: keyData, encoding: .utf8) ?? "HTTP \(httpResp.statusCode)"
                payload.errorMessage = "Auth failed: \(msg)"
                return payload
            }

            let decodedKey = try JSONDecoder().decode(OpenRouterKeyResponse.self, from: keyData)
            if let d = decodedKey.data {
                payload.keyLabel = d.label ?? "Key"
                payload.keyUsage = d.usage ?? 0.0
                payload.keyLimit = d.limit
                if let lim = d.limit {
                    payload.keyRemaining = max(0.0, lim - (d.usage ?? 0.0))
                }
                payload.usageDaily = d.usage_daily
                payload.usageWeekly = d.usage_weekly
                payload.usageMonthly = d.usage_monthly
                payload.isFreeTier = d.is_free_tier ?? false
            }
        } catch {
            payload.errorMessage = "Network err: \(error.localizedDescription)"
            return payload
        }

        // 2. Account Credits & Balance
        do {
            if let creditsURL = URL(string: "https://openrouter.ai/api/v1/credits") {
                var creditsReq = URLRequest(url: creditsURL)
                creditsReq.setValue("Bearer \(cleanKey)", forHTTPHeaderField: "Authorization")
                creditsReq.setValue("OpenRouterTracker/2.0", forHTTPHeaderField: "User-Agent")

                let (cData, cResp) = try await session.data(for: creditsReq)
                if let httpResp = cResp as? HTTPURLResponse, httpResp.statusCode == 200 {
                    let decodedCredits = try JSONDecoder().decode(OpenRouterCreditsResponse.self, from: cData)
                    if let cd = decodedCredits.data {
                        let total = cd.total_credits ?? 0.0
                        let used = cd.total_usage ?? 0.0
                        payload.totalCredits = total
                        payload.totalUsage = used
                        payload.totalBalance = max(0.0, total - used)
                    }
                }
            }
        } catch {
            // Account endpoint failure is non-fatal for key stats
        }

        return payload
    }

    @discardableResult
    public static func refreshKey(_ key: TrackedKey) async -> WidgetPayload {
        guard let rawKey = SharedStorage.getRawAPIKey(for: key.id) else {
            var empty = WidgetPayload.empty
            empty.customNickname = key.customLabel
            empty.keyMasked = key.keyMasked
            return empty
        }

        let payload = await fetchData(apiKey: rawKey, customNickname: key.customLabel)
        SharedStorage.savePayload(payload, for: key.id)

        if key.isWidgetKey {
            SharedStorage.saveWidgetPayload(payload)
        }

        return payload
    }

    @discardableResult
    public static func refreshWidgetKey() async -> WidgetPayload {
        guard let widgetKey = SharedStorage.getWidgetKey() else {
            return WidgetPayload.empty
        }
        return await refreshKey(widgetKey)
    }
}
