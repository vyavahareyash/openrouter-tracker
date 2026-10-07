import Foundation

public struct SharedStorage {
    public static let suiteName = "group.com.openrouter.tracker"
    private static let keyAPIKey = "openrouter_api_key"
    private static let keyPayload = "openrouter_widget_payload"

    private static var userDefaults: UserDefaults {
        UserDefaults(suiteName: suiteName) ?? UserDefaults.standard
    }

    public static func saveAPIKey(_ key: String) {
        let clean = key.trimmingCharacters(in: .whitespacesAndNewlines)
        userDefaults.set(clean, forKey: keyAPIKey)
        UserDefaults.standard.set(clean, forKey: keyAPIKey)
    }

    public static func getAPIKey() -> String? {
        if let key = userDefaults.string(forKey: keyAPIKey), !key.isEmpty {
            return key
        }
        if let key = UserDefaults.standard.string(forKey: keyAPIKey), !key.isEmpty {
            return key
        }
        // Fallback: check environment variable
        if let envKey = ProcessInfo.processInfo.environment["OPENROUTER_API_KEY"], !envKey.isEmpty {
            return envKey
        }
        return nil
    }

    public static func savePayload(_ payload: WidgetPayload) {
        if let data = try? JSONEncoder().encode(payload) {
            userDefaults.set(data, forKey: keyPayload)
            UserDefaults.standard.set(data, forKey: keyPayload)
        }
    }

    public static func getPayload() -> WidgetPayload? {
        if let data = userDefaults.data(forKey: keyPayload),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }
        if let data = UserDefaults.standard.data(forKey: keyPayload),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }
        return nil
    }
}
