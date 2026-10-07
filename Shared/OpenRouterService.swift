import Foundation

public struct OpenRouterService {
    public static func fetchData() async -> WidgetPayload {
        guard let apiKey = SharedStorage.getAPIKey(), !apiKey.isEmpty else {
            return WidgetPayload.empty
        }

        var payload = WidgetPayload(
            keyLabel: "Unknown",
            keyUsage: 0.0,
            keyLimit: nil,
            keyRemaining: nil,
            totalCredits: 0.0,
            totalUsage: 0.0,
            totalBalance: 0.0,
            isFreeTier: false,
            lastUpdated: Date(),
            errorMessage: nil
        )

        // 1. Fetch Key Details
        do {
            guard let keyURL = URL(string: "https://openrouter.ai/api/v1/auth/key") else {
                throw URLError(.badURL)
            }
            var keyReq = URLRequest(url: keyURL)
            keyReq.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
            keyReq.setValue("OpenRouterWidget/1.0", forHTTPHeaderField: "User-Agent")
            keyReq.timeoutInterval = 10

            let (keyData, keyResp) = try await URLSession.shared.data(for: keyReq)
            if let httpResp = keyResp as? HTTPURLResponse, httpResp.statusCode != 200 {
                let msg = String(data: keyData, encoding: .utf8) ?? "HTTP \(httpResp.statusCode)"
                payload.errorMessage = "Auth: \(msg)"
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
                payload.isFreeTier = d.is_free_tier ?? false
            }
        } catch {
            payload.errorMessage = "Key err: \(error.localizedDescription)"
            return payload
        }

        // 2. Fetch Account Credits (optional)
        do {
            if let creditsURL = URL(string: "https://openrouter.ai/api/v1/credits") {
                var creditsReq = URLRequest(url: creditsURL)
                creditsReq.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
                creditsReq.setValue("OpenRouterWidget/1.0", forHTTPHeaderField: "User-Agent")
                creditsReq.timeoutInterval = 10

                let (cData, cResp) = try await URLSession.shared.data(for: creditsReq)
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
            // Optional endpoint failure is non-fatal
        }

        return payload
    }

    @discardableResult
    public static func refreshAndSave() async -> WidgetPayload {
        let payload = await fetchData()
        SharedStorage.savePayload(payload)
        return payload
    }
}
