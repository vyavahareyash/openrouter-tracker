import SwiftUI
import WidgetKit

struct ContentView: View {
    @State private var apiKeyInput: String = ""
    @State private var statusMessage: String = ""
    @State private var isTesting: Bool = false
    @State private var cachedPayload: WidgetPayload?

    var body: some View {
        VStack(spacing: 20) {
            // Header
            HStack(spacing: 12) {
                Image(systemName: "gauge.with.dots.needle.bottom.50percent")
                    .font(.system(size: 32))
                    .foregroundStyle(.blue)
                VStack(alignment: .leading) {
                    Text("OpenRouter Tracker")
                        .font(.title2.bold())
                    Text("macOS Desktop Widget Configuration")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }

            Divider()

            // Key Input & Actions
            VStack(alignment: .leading, spacing: 8) {
                Text("OpenRouter API Key:")
                    .font(.headline)

                HStack {
                    SecureField("sk-or-v1-...", text: $apiKeyInput)
                        .textFieldStyle(.roundedBorder)

                    Button("Save Key") {
                        saveKey()
                    }
                    .keyboardShortcut(.defaultAction)
                }

                if !statusMessage.isEmpty {
                    Text(statusMessage)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }

            // Quick Test & Stats Card
            if let payload = cachedPayload {
                VStack(spacing: 8) {
                    HStack {
                        Text("Active Stats Preview")
                            .font(.subheadline.bold())
                        Spacer()
                        Text("Updated: \(payload.lastUpdated.formatted(date: .omitted, time: .standard))")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }

                    HStack(spacing: 20) {
                        StatTile(label: "Balance", value: String(format: "$%.2f", payload.totalBalance), color: .blue)
                        StatTile(label: "Key Usage", value: String(format: "$%.4f", payload.keyUsage), color: .purple)
                        StatTile(label: "Key Limit", value: payload.keyLimit != nil ? String(format: "$%.2f", payload.keyLimit!) : "Unlimited", color: .orange)
                    }
                }
                .padding()
                .background(Color(nsColor: .controlBackgroundColor))
                .cornerRadius(8)
            }

            HStack {
                Button(action: testAndRefresh) {
                    if isTesting {
                        ProgressView()
                            .scaleEffect(0.6)
                    } else {
                        Label("Test API & Reload Widget", systemImage: "arrow.clockwise")
                    }
                }
                .disabled(isTesting || apiKeyInput.isEmpty)

                Spacer()
            }

            Divider()

            // Instructions
            VStack(alignment: .leading, spacing: 6) {
                Text("How to add widget to your Desktop:")
                    .font(.subheadline.bold())
                Text("1. Right-click any empty space on your Mac Desktop.")
                    .font(.footnote)
                Text("2. Click 'Edit Widgets...'")
                    .font(.footnote)
                Text("3. Search for 'OpenRouter' and drag the widget onto your desktop.")
                    .font(.footnote)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(Color.blue.opacity(0.08))
            .cornerRadius(8)
        }
        .padding(24)
        .frame(width: 520, height: 480)
        .onAppear {
            loadInitialKey()
        }
    }

    private func loadInitialKey() {
        if let key = SharedStorage.getAPIKey() {
            apiKeyInput = key
            cachedPayload = SharedStorage.getPayload()
            statusMessage = "Loaded existing API key."
        } else {
            // Check if .env file exists in working dir or home
            let cwd = FileManager.default.currentDirectoryPath
            let envURL = URL(fileURLWithPath: cwd).appendingPathComponent(".env")
            if let content = try? String(contentsOf: envURL, encoding: .utf8) {
                for line in content.components(separatedBy: .newlines) {
                    if line.starts(with: "OPENROUTER_API_KEY=") {
                        let val = line.replacingOccurrences(of: "OPENROUTER_API_KEY=", with: "")
                            .trimmingCharacters(in: .whitespacesAndNewlines)
                            .trimmingCharacters(in: CharacterSet(charactersIn: "\"'"))
                        if !val.isEmpty {
                            apiKeyInput = val
                            saveKey()
                            statusMessage = "Loaded key automatically from .env"
                            break
                        }
                    }
                }
            }
        }
    }

    private func saveKey() {
        guard !apiKeyInput.isEmpty else { return }
        SharedStorage.saveAPIKey(apiKeyInput)
        statusMessage = "Key saved to shared storage."
        testAndRefresh()
    }

    private func testAndRefresh() {
        isTesting = true
        statusMessage = "Connecting to OpenRouter..."
        Task {
            let payload = await OpenRouterService.refreshAndSave()
            await MainActor.run {
                isTesting = false
                cachedPayload = payload
                if let err = payload.errorMessage {
                    statusMessage = "❌ Error: \(err)"
                } else {
                    statusMessage = "✅ Connection successful! Widget timeline refreshed."
                    WidgetCenter.shared.reloadAllTimelines()
                }
            }
        }
    }
}

struct StatTile: View {
    let label: String
    let value: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 16, weight: .bold, design: .rounded))
                .foregroundStyle(color)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}
