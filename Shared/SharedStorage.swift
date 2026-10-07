import Foundation

public struct SharedStorage {
    private static let keyFileName = "openrouter_key.txt"
    private static let payloadFileName = "openrouter_payload.json"
    private static let keyAPIKey = "openrouter_api_key"
    private static let keyPayload = "openrouter_widget_payload"

    public static var storageDirectory: URL {
        let home = NSHomeDirectory()
        let targetPath: String
        if home.contains("com.openrouter.tracker.widget") {
            // Inside widget extension sandbox container
            targetPath = home
        } else if let range = home.range(of: "/Library/Containers") {
            // Inside another sandbox container
            let realHome = String(home[..<range.lowerBound])
            targetPath = "\(realHome)/Library/Containers/com.openrouter.tracker.widget/Data"
        } else {
            // Non-sandboxed host app (real user home)
            targetPath = "\(home)/Library/Containers/com.openrouter.tracker.widget/Data"
        }
        let url = URL(fileURLWithPath: targetPath)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    private static var keyFileURL: URL {
        storageDirectory.appendingPathComponent(keyFileName)
    }

    private static var payloadFileURL: URL {
        storageDirectory.appendingPathComponent(payloadFileName)
    }

    public static func saveAPIKey(_ key: String) {
        let clean = key.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !clean.isEmpty else { return }

        UserDefaults.standard.set(clean, forKey: keyAPIKey)
        try? clean.write(to: keyFileURL, atomically: true, encoding: .utf8)
    }

    public static func getAPIKey() -> String? {
        // 1. Direct file in widget container (works across ad-hoc processes)
        if let fileContent = try? String(contentsOf: keyFileURL, encoding: .utf8) {
            let trimmed = fileContent.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmed.isEmpty {
                return trimmed
            }
        }

        // 2. UserDefaults
        if let key = UserDefaults.standard.string(forKey: keyAPIKey), !key.isEmpty {
            return key
        }

        // 3. Process environment
        if let envKey = ProcessInfo.processInfo.environment["OPENROUTER_API_KEY"], !envKey.isEmpty {
            return envKey
        }

        return nil
    }

    public static func savePayload(_ payload: WidgetPayload) {
        if let data = try? JSONEncoder().encode(payload) {
            UserDefaults.standard.set(data, forKey: keyPayload)
            try? data.write(to: payloadFileURL, options: .atomic)
        }
    }

    public static func getPayload() -> WidgetPayload? {
        // 1. Direct file in widget container
        if let data = try? Data(contentsOf: payloadFileURL),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }

        // 2. UserDefaults
        if let data = UserDefaults.standard.data(forKey: keyPayload),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }

        return nil
    }
}
