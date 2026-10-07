import Foundation

public struct MockData {
    public static let primaryKeyId = UUID(uuidString: "11111111-1111-1111-1111-111111111111")!
    public static let devKeyId = UUID(uuidString: "22222222-2222-2222-2222-222222222222")!
    public static let warningKeyId = UUID(uuidString: "33333333-3333-3333-3333-333333333333")!
    public static let unlimitedKeyId = UUID(uuidString: "44444444-4444-4444-4444-444444444444")!

    public static let sampleKeys: [TrackedKey] = [
        TrackedKey(
            id: primaryKeyId,
            customLabel: "Production Backend",
            apiKey: "sk-or-v1-prod89abcdef0123456789abcdef",
            isWidgetKey: true,
            createdAt: Date(timeIntervalSince1970: 1700000000)
        ),
        TrackedKey(
            id: devKeyId,
            customLabel: "Dev & Staging",
            apiKey: "sk-or-v1-dev9876543210fedcba98765432",
            isWidgetKey: false,
            createdAt: Date(timeIntervalSince1970: 1700500000)
        ),
        TrackedKey(
            id: warningKeyId,
            customLabel: "Background Workers",
            apiKey: "sk-or-v1-wrk112233445566778899aabbcc",
            isWidgetKey: false,
            createdAt: Date(timeIntervalSince1970: 1701000000)
        ),
        TrackedKey(
            id: unlimitedKeyId,
            customLabel: "Research & Evals",
            apiKey: "sk-or-v1-eval99887766554433221100ffaa",
            isWidgetKey: false,
            createdAt: Date(timeIntervalSince1970: 1701500000)
        )
    ]

    public static let primaryPayload = WidgetPayload(
        keyLabel: "sk-or-v1-prod...",
        customNickname: "Production Backend",
        keyMasked: "sk-or-v1...cdef",
        keyUsage: 18.4250,
        keyLimit: 25.00,
        keyRemaining: 6.5750,
        usageDaily: 1.8420,
        usageWeekly: 8.9240,
        usageMonthly: 18.4250,
        totalCredits: 250.00,
        totalUsage: 84.20,
        totalBalance: 165.80,
        isFreeTier: false,
        lastUpdated: Date(),
        errorMessage: nil
    )

    public static let devPayload = WidgetPayload(
        keyLabel: "sk-or-v1-dev...",
        customNickname: "Dev & Staging",
        keyMasked: "sk-or-v1...5432",
        keyUsage: 1.1200,
        keyLimit: 5.00,
        keyRemaining: 3.8800,
        usageDaily: 0.1500,
        usageWeekly: 0.7200,
        usageMonthly: 1.1200,
        totalCredits: 250.00,
        totalUsage: 84.20,
        totalBalance: 165.80,
        isFreeTier: false,
        lastUpdated: Date(),
        errorMessage: nil
    )

    public static let warningPayload = WidgetPayload(
        keyLabel: "sk-or-v1-wrk...",
        customNickname: "Background Workers",
        keyMasked: "sk-or-v1...bbcc",
        keyUsage: 4.6500,
        keyLimit: 5.00,
        keyRemaining: 0.3500,
        usageDaily: 0.9500,
        usageWeekly: 3.2000,
        usageMonthly: 4.6500,
        totalCredits: 250.00,
        totalUsage: 84.20,
        totalBalance: 165.80,
        isFreeTier: false,
        lastUpdated: Date(),
        errorMessage: nil
    )

    public static let unlimitedPayload = WidgetPayload(
        keyLabel: "sk-or-v1-eval...",
        customNickname: "Research & Evals",
        keyMasked: "sk-or-v1...ffaa",
        keyUsage: 12.8000,
        keyLimit: nil,
        keyRemaining: nil,
        usageDaily: 2.1000,
        usageWeekly: 6.5000,
        usageMonthly: 12.8000,
        totalCredits: 250.00,
        totalUsage: 84.20,
        totalBalance: 165.80,
        isFreeTier: false,
        lastUpdated: Date(),
        errorMessage: nil
    )

    public static let samplePayloads: [UUID: WidgetPayload] = [
        primaryKeyId: primaryPayload,
        devKeyId: devPayload,
        warningKeyId: warningPayload,
        unlimitedKeyId: unlimitedPayload
    ]

    public static var defaultWidgetPayload: WidgetPayload {
        primaryPayload
    }
}
