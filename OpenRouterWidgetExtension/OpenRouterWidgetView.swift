import SwiftUI
import WidgetKit

struct OpenRouterWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    var entry: OpenRouterTimelineEntry

    var body: some View {
        switch family {
        case .systemMedium:
            MediumView(payload: entry.payload)
        default:
            SmallView(payload: entry.payload)
        }
    }
}

// MARK: - Small Widget View
struct SmallView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header
            HStack {
                Text("OpenRouter")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                Button(intent: RefreshBalanceIntent()) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundStyle(.primary)
                }
                .buttonStyle(.plain)
            }

            if let err = payload.errorMessage {
                Spacer()
                Text("⚠️ \(err)")
                    .font(.system(size: 10))
                    .foregroundStyle(.red)
                    .lineLimit(3)
                Spacer()
            } else {
                Spacer()
                // Main Balance
                VStack(alignment: .leading, spacing: 1) {
                    Text("Balance")
                        .font(.system(size: 10, weight: .medium))
                        .foregroundStyle(.secondary)
                    Text(String(format: "$%.2f", payload.totalBalance))
                        .font(.system(size: 22, weight: .bold, design: .rounded))
                        .foregroundStyle(.primary)
                }

                Divider().opacity(0.4)

                // Key Limit / Usage
                VStack(alignment: .leading, spacing: 2) {
                    HStack {
                        Text("Usage:")
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(String(format: "$%.4f", payload.keyUsage))
                            .font(.system(size: 9, weight: .semibold, design: .monospaced))
                    }
                    if let limit = payload.keyLimit {
                        HStack {
                            Text("Limit:")
                                .font(.system(size: 9))
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(String(format: "$%.2f", limit))
                                .font(.system(size: 9, weight: .semibold, design: .monospaced))
                        }
                    }
                }
            }
        }
        .padding(12)
        .containerBackground(for: .widget) {
            Color(nsColor: .windowBackgroundColor)
        }
    }
}

// MARK: - Medium Widget View
struct MediumView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header
            HStack {
                HStack(spacing: 5) {
                    Image(systemName: "bolt.horizontal.fill")
                        .font(.system(size: 11))
                        .foregroundStyle(.blue)
                    Text("OpenRouter API")
                        .font(.system(size: 12, weight: .bold))
                }
                Spacer()
                Text(payload.lastUpdated, style: .time)
                    .font(.system(size: 10))
                    .foregroundStyle(.secondary)
                Button(intent: RefreshBalanceIntent()) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 12, weight: .bold))
                        .foregroundStyle(.blue)
                }
                .buttonStyle(.plain)
            }

            if let err = payload.errorMessage {
                Spacer()
                Text("⚠️ \(err)")
                    .font(.system(size: 11))
                    .foregroundStyle(.red)
                Spacer()
            } else {
                HStack(alignment: .top, spacing: 16) {
                    // Left Column: Account Balance
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Total Balance")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(.secondary)
                        Text(String(format: "$%.2f", payload.totalBalance))
                            .font(.system(size: 26, weight: .bold, design: .rounded))
                            .foregroundStyle(.primary)

                        Text("Credits: $\(String(format: "%.2f", payload.totalCredits))")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                        Text("Acc Used: $\(String(format: "%.2f", payload.totalUsage))")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                    }

                    Spacer()
                    Divider().opacity(0.4)
                    Spacer()

                    // Right Column: Key Details
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Key Details")
                            .font(.system(size: 11, weight: .medium))
                            .foregroundStyle(.secondary)
                        Text(payload.keyLabel)
                            .font(.system(size: 11, weight: .semibold))
                            .lineLimit(1)
                            .truncationMode(.middle)

                        HStack {
                            Text("Key Used:")
                                .font(.system(size: 10))
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text(String(format: "$%.4f", payload.keyUsage))
                                .font(.system(size: 10, weight: .semibold, design: .monospaced))
                        }
                        if let remaining = payload.keyRemaining {
                            HStack {
                                Text("Remaining:")
                                    .font(.system(size: 10))
                                    .foregroundStyle(.secondary)
                                Spacer()
                                Text(String(format: "$%.4f", remaining))
                                    .font(.system(size: 10, weight: .semibold, design: .monospaced))
                                    .foregroundStyle(.green)
                            }
                        }
                    }
                    .frame(minWidth: 130)
                }
            }
        }
        .padding(12)
        .containerBackground(for: .widget) {
            Color(nsColor: .windowBackgroundColor)
        }
    }
}
