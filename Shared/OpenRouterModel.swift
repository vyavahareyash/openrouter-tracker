import Foundation

public struct OpenRouterKeyResponse: Codable {
    public struct DataClass: Codable {
        public let label: String?
        public let usage: Double?
        public let limit: Double?
        public let is_free_tier: Bool?
        public let usage_daily: Double?
        public let usage_weekly: Double?
        public let usage_monthly: Double?
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

public struct TrackedKey: Codable, Identifiable, Equatable {
    public var id: UUID
    public var customLabel: String
    public var keyMasked: String
    public var isWidgetKey: Bool
    public var createdAt: Date

    public init(
        id: UUID = UUID(),
        customLabel: String,
        apiKey: String,
        isWidgetKey: Bool = false,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.customLabel = customLabel
        self.keyMasked = TrackedKey.mask(apiKey)
        self.isWidgetKey = isWidgetKey
        self.createdAt = createdAt
    }

    public static func mask(_ key: String) -> String {
        let trimmed = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard trimmed.count > 12 else { return "••••••••" }
        let prefix = trimmed.prefix(8)
        let suffix = trimmed.suffix(4)
        return "\(prefix)...\(suffix)"
    }
}

public struct WidgetPayload: Codable, Equatable {
    public var keyLabel: String
    public var customNickname: String
    public var keyMasked: String
    public var keyUsage: Double
    public var keyLimit: Double?
    public var keyRemaining: Double?
    public var usageDaily: Double?
    public var usageWeekly: Double?
    public var usageMonthly: Double?
    public var totalCredits: Double
    public var totalUsage: Double
    public var totalBalance: Double
    public var isFreeTier: Bool
    public var lastUpdated: Date
    public var errorMessage: String?

    public var usagePercent: Double {
        guard let limit = keyLimit, limit > 0 else { return 0.0 }
        return min(1.0, max(0.0, keyUsage / limit))
    }

    public var accountBurnPercent: Double {
        guard totalCredits > 0 else { return 0.0 }
        return min(1.0, max(0.0, totalUsage / totalCredits))
    }

    public static var placeholder: WidgetPayload {
        WidgetPayload(
            keyLabel: "sk-or-v1-...",
            customNickname: "Default Key",
            keyMasked: "sk-or-v1-...59f",
            keyUsage: 3.46,
            keyLimit: 5.0,
            keyRemaining: 1.54,
            usageDaily: 0.85,
            usageWeekly: 2.10,
            usageMonthly: 3.46,
            totalCredits: 605.0,
            totalUsage: 133.90,
            totalBalance: 471.10,
            isFreeTier: false,
            lastUpdated: Date(),
            errorMessage: nil
        )
    }

    public static var empty: WidgetPayload {
        WidgetPayload(
            keyLabel: "Not Configured",
            customNickname: "No Key",
            keyMasked: "None",
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
            errorMessage: "API key not configured"
        )
    }
}

// MARK: - OpenRouter Unified Design Tokens
import SwiftUI

public struct OpenRouterTheme {
    public static let electricBlue = Color(red: 0.23, green: 0.51, blue: 0.96) // #3B82F6
    public static let neonViolet = Color(red: 0.66, green: 0.34, blue: 0.96)   // #A855F7
    public static let emeraldGreen = Color(red: 0.06, green: 0.73, blue: 0.51) // #10B981
    public static let amberWarning = Color(red: 0.96, green: 0.62, blue: 0.04) // #F59E0B
    public static let coralRed = Color(red: 0.94, green: 0.27, blue: 0.27)     // #EF4444

    public static let routerGradient = LinearGradient(
        colors: [electricBlue, neonViolet],
        startPoint: .topLeading,
        endPoint: .bottomTrailing
    )

    public static func gaugeStroke(usagePercent: Double) -> AnyShapeStyle {
        if usagePercent > 0.9 {
            return AnyShapeStyle(coralRed)
        } else if usagePercent > 0.75 {
            return AnyShapeStyle(amberWarning)
        } else {
            return AnyShapeStyle(routerGradient)
        }
    }
}

extension WidgetPayload {
    public var gaugeStrokeGradient: AnyShapeStyle {
        OpenRouterTheme.gaugeStroke(usagePercent: usagePercent)
    }
}
