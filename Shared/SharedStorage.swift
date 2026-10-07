import Foundation

public struct SharedStorage {
    private static let keysMetaFileName = "keys_meta.json"
    private static let widgetPayloadFileName = "openrouter_payload.json"
    private static let legacyKeyFileName = "openrouter_key.txt"

    public static var storageDirectory: URL {
        let home = NSHomeDirectory()
        let targetPath: String
        if home.contains("com.openrouter.tracker.widget") {
            targetPath = home
        } else if let range = home.range(of: "/Library/Containers") {
            let realHome = String(home[..<range.lowerBound])
            targetPath = "\(realHome)/Library/Containers/com.openrouter.tracker.widget/Data"
        } else {
            targetPath = "\(home)/Library/Containers/com.openrouter.tracker.widget/Data"
        }
        let url = URL(fileURLWithPath: targetPath)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        return url
    }

    private static var keysMetaFileURL: URL {
        storageDirectory.appendingPathComponent(keysMetaFileName)
    }

    private static var widgetPayloadFileURL: URL {
        storageDirectory.appendingPathComponent(widgetPayloadFileName)
    }

    private static func payloadFileURL(for id: UUID) -> URL {
        storageDirectory.appendingPathComponent("payload_\(id.uuidString).json")
    }

    // MARK: - Multi-Key Management

    public static func loadAllKeys() -> [TrackedKey] {
        if let data = try? Data(contentsOf: keysMetaFileURL),
           let keys = try? JSONDecoder().decode([TrackedKey].self, from: data),
           !keys.isEmpty {
            return keys
        }

        // Migration: If no keys saved yet, check legacy file or .env
        if let legacyKey = loadLegacyKey(), !legacyKey.isEmpty {
            let initial = TrackedKey(
                customLabel: "Primary Key",
                apiKey: legacyKey,
                isWidgetKey: true
            )
            saveRawAPIKey(legacyKey, for: initial.id)
            saveKeysMeta([initial])
            return [initial]
        }

        return []
    }

    public static func addKey(customLabel: String, apiKey: String, isWidgetKey: Bool) -> TrackedKey {
        var keys = loadAllKeys()
        let shouldBeWidget = isWidgetKey || keys.isEmpty

        if shouldBeWidget {
            for i in 0..<keys.count {
                keys[i].isWidgetKey = false
            }
        }

        let newKey = TrackedKey(
            customLabel: customLabel.isEmpty ? "API Key \(keys.count + 1)" : customLabel,
            apiKey: apiKey,
            isWidgetKey: shouldBeWidget
        )

        saveRawAPIKey(apiKey, for: newKey.id)
        keys.append(newKey)
        saveKeysMeta(keys)

        if shouldBeWidget {
            // Keep legacy file updated with widget key for extension compatibility
            try? apiKey.trimmingCharacters(in: .whitespacesAndNewlines).write(
                to: storageDirectory.appendingPathComponent(legacyKeyFileName),
                atomically: true,
                encoding: .utf8
            )
        }

        return newKey
    }

    public static func updateKey(_ key: TrackedKey) {
        var keys = loadAllKeys()
        guard let idx = keys.firstIndex(where: { $0.id == key.id }) else { return }

        if key.isWidgetKey {
            for i in 0..<keys.count {
                keys[i].isWidgetKey = false
            }
        }

        keys[idx] = key
        saveKeysMeta(keys)

        if key.isWidgetKey, let raw = getRawAPIKey(for: key.id) {
            try? raw.write(
                to: storageDirectory.appendingPathComponent(legacyKeyFileName),
                atomically: true,
                encoding: .utf8
            )
        }
    }

    public static func deleteKey(id: UUID) {
        var keys = loadAllKeys()
        guard let idx = keys.firstIndex(where: { $0.id == id }) else { return }

        let wasWidget = keys[idx].isWidgetKey
        keys.remove(at: idx)

        // Delete secrets
        KeychainHelper.delete(for: id.uuidString)
        try? FileManager.default.removeItem(at: payloadFileURL(for: id))
        let secretFile = storageDirectory.appendingPathComponent("secret_\(id.uuidString).txt")
        try? FileManager.default.removeItem(at: secretFile)

        if wasWidget && !keys.isEmpty {
            keys[0].isWidgetKey = true
            if let newWidgetRaw = getRawAPIKey(for: keys[0].id) {
                try? newWidgetRaw.write(
                    to: storageDirectory.appendingPathComponent(legacyKeyFileName),
                    atomically: true,
                    encoding: .utf8
                )
            }
        }

        saveKeysMeta(keys)
    }

    public static func setWidgetKey(id: UUID) {
        var keys = loadAllKeys()
        for i in 0..<keys.count {
            keys[i].isWidgetKey = (keys[i].id == id)
        }
        saveKeysMeta(keys)

        if let raw = getRawAPIKey(for: id) {
            try? raw.write(
                to: storageDirectory.appendingPathComponent(legacyKeyFileName),
                atomically: true,
                encoding: .utf8
            )
        }

        if let payload = getPayload(for: id) {
            saveWidgetPayload(payload)
        }
    }

    public static func getWidgetKey() -> TrackedKey? {
        let keys = loadAllKeys()
        return keys.first(where: { $0.isWidgetKey }) ?? keys.first
    }

    // MARK: - Secret Key Storage (Keychain with 0600 File Fallback)

    public static func saveRawAPIKey(_ key: String, for id: UUID) {
        let clean = key.trimmingCharacters(in: .whitespacesAndNewlines)
        KeychainHelper.save(key: clean, for: id.uuidString)

        // Secure file fallback with POSIX 0600 permissions
        let secretFile = storageDirectory.appendingPathComponent("secret_\(id.uuidString).txt")
        try? clean.write(to: secretFile, atomically: true, encoding: .utf8)
        try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: secretFile.path)
    }

    public static func getRawAPIKey(for id: UUID) -> String? {
        if let key = KeychainHelper.get(for: id.uuidString), !key.isEmpty {
            return key
        }
        let secretFile = storageDirectory.appendingPathComponent("secret_\(id.uuidString).txt")
        if let content = try? String(contentsOf: secretFile, encoding: .utf8) {
            let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmed.isEmpty { return trimmed }
        }
        return nil
    }

    // MARK: - Payload Caching

    public static func savePayload(_ payload: WidgetPayload, for id: UUID) {
        let url = payloadFileURL(for: id)
        if let data = try? JSONEncoder().encode(payload) {
            try? data.write(to: url, options: .atomic)
            try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: url.path)
        }
    }

    public static func getPayload(for id: UUID) -> WidgetPayload? {
        let url = payloadFileURL(for: id)
        if let data = try? Data(contentsOf: url),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }
        return nil
    }

    public static func saveWidgetPayload(_ payload: WidgetPayload) {
        if let data = try? JSONEncoder().encode(payload) {
            try? data.write(to: widgetPayloadFileURL, options: .atomic)
            try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: widgetPayloadFileURL.path)
        }
    }

    public static func getWidgetPayload() -> WidgetPayload? {
        if let data = try? Data(contentsOf: widgetPayloadFileURL),
           let payload = try? JSONDecoder().decode(WidgetPayload.self, from: data) {
            return payload
        }
        return nil
    }

    // MARK: - Internal Helpers

    private static func saveKeysMeta(_ keys: [TrackedKey]) {
        if let data = try? JSONEncoder().encode(keys) {
            try? data.write(to: keysMetaFileURL, options: .atomic)
            try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: keysMetaFileURL.path)
        }
    }

    private static func loadLegacyKey() -> String? {
        let legacyFile = storageDirectory.appendingPathComponent(legacyKeyFileName)
        if let content = try? String(contentsOf: legacyFile, encoding: .utf8) {
            let trimmed = content.trimmingCharacters(in: .whitespacesAndNewlines)
            if !trimmed.isEmpty { return trimmed }
        }
        return nil
    }
}
