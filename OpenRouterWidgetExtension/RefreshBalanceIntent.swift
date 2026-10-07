import AppIntents
import Foundation
import WidgetKit

public struct RefreshBalanceIntent: AppIntent {
    public static var title: LocalizedStringResource = "Refresh OpenRouter Balance"
    public static var description = IntentDescription("Refreshes OpenRouter key usage and account balance")

    public init() {}

    public func perform() async throws -> some IntentResult {
        await OpenRouterService.refreshAndSave()
        WidgetCenter.shared.reloadAllTimelines()
        return .result()
    }
}
