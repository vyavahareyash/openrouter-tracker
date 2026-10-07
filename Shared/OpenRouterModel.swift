import Foundation

public struct OpenRouterKeyResponse: Codable {
    public struct DataClass: Codable {
        public let label: String?
        public let usage: Double?
        public let limit: Double?
        public let is_free_tier: Bool?
    }
    public let data: DataClass?
}

public struct OpenRouterCreditsResponse: Codable {
    public struct DataClass: Codable {
        public let total_credits: Double?
        public let total_usage: Double?
    }
    public let data: DataClass?
}

public struct WidgetPayload: Codable {
    public var keyLabel: String
    public var keyUsage: Double
    public var keyLimit: Double?
    public var keyRemaining: Double?
    public var totalCredits: Double
    public var totalUsage: Double
    public var totalBalance: Double
    public var isFreeTier: Bool
    public var lastUpdated: Date
    public var errorMessage: String?

    public static var placeholder: WidgetPayload {
        WidgetPayload(
            keyLabel: "sk-or-v1-...",
            keyUsage: 0.0,
            keyLimit: 5.0,
            keyRemaining: 5.0,
            totalCredits: 605.0,
            totalUsage: 96.15,
            totalBalance: 508.85,
            isFreeTier: false,
            lastUpdated: Date(),
            errorMessage: nil
        )
    }

    public static var empty: WidgetPayload {
        WidgetPayload(
            keyLabel: "Not Set",
            keyUsage: 0.0,
            keyLimit: nil,
            keyRemaining: nil,
            totalCredits: 0.0,
            totalUsage: 0.0,
            totalBalance: 0.0,
            isFreeTier: false,
            lastUpdated: Date(),
            errorMessage: "API key not configured"
        )
    }
}
