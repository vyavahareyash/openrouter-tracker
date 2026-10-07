import SwiftUI
import WidgetKit

struct OpenRouterWidgetEntryView: View {
    @Environment(\.widgetFamily) var family
    var entry: OpenRouterTimelineEntry

    var body: some View {
        switch family {
        case .systemMedium:
            MediumWidgetView(payload: entry.payload)
        default:
            SmallWidgetView(payload: entry.payload)
        }
    }
}

// MARK: - Small Widget View
struct SmallWidgetView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Header: Nickname + Refresh
            HStack {
                Text(payload.customNickname)
                    .font(.system(size: 11, weight: .bold))
                    .lineLimit(1)
                Spacer()
                Button(intent: RefreshBalanceIntent()) {
                    Image(systemName: "arrow.clockwise")
                        .font(.system(size: 11, weight: .bold))
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
                // Visual Budget Progress
                if let limit = payload.keyLimit, limit > 0 {
                    HStack(spacing: 10) {
                        // Circular Ring Gauge
                        ZStack {
                            Circle()
                                .stroke(Color.secondary.opacity(0.2), lineWidth: 5)
                            Circle()
                                .trim(from: 0, to: CGFloat(payload.usagePercent))
                                .stroke(
                                    payload.usagePercent > 0.9 ? Color.red : (payload.usagePercent > 0.75 ? Color.orange : Color.purple),
                                    style: StrokeStyle(lineWidth: 5, lineCap: .round)
                                )
                                .rotationEffect(.degrees(-90))
                            Text("\(Int(payload.usagePercent * 100))%")
                                .font(.system(size: 9, weight: .bold))
                        }
                        .frame(width: 38, height: 38)

                        VStack(alignment: .leading, spacing: 1) {
                            Text("Key Remaining")
                                .font(.system(size: 9))
                                .foregroundStyle(.secondary)
                            Text(String(format: "$%.2f", payload.keyRemaining ?? 0.0))
                                .font(.system(size: 14, weight: .bold, design: .rounded))
                                .foregroundStyle(.green)
                        }
                    }
                } else {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Key Used (Unlimited)")
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                        Text(String(format: "$%.4f", payload.keyUsage))
                            .font(.system(size: 16, weight: .bold, design: .rounded))
                    }
                }

                Divider().opacity(0.3)

                // Sub-stats
                HStack {
                    Text("Used: $\(String(format: "%.2f", payload.keyUsage))")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                    Spacer()
                    if let lim = payload.keyLimit {
                        Text("Cap: $\(String(format: "%.2f", lim))")
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
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
struct MediumWidgetView: View {
    let payload: WidgetPayload

    var body: some View {
        HStack(spacing: 12) {
            // LEFT COLUMN: Key-Specific Metrics (Primary)
            VStack(alignment: .leading, spacing: 6) {
                HStack(spacing: 5) {
                    Circle()
                        .fill(Color.purple)
                        .frame(width: 7, height: 7)
                    Text(payload.customNickname)
                        .font(.system(size: 12, weight: .bold))
                        .lineLimit(1)
                }

                Text(payload.keyMasked)
                    .font(.system(size: 9, design: .monospaced))
                    .foregroundStyle(.secondary)

                Spacer()

                if let limit = payload.keyLimit, limit > 0 {
                    HStack(spacing: 10) {
                        // Ring
                        ZStack {
                            Circle()
                                .stroke(Color.secondary.opacity(0.2), lineWidth: 5.5)
                            Circle()
                                .trim(from: 0, to: CGFloat(payload.usagePercent))
                                .stroke(
                                    payload.usagePercent > 0.9 ? Color.red : (payload.usagePercent > 0.75 ? Color.orange : Color.purple),
                                    style: StrokeStyle(lineWidth: 5.5, lineCap: .round)
                                )
                                .rotationEffect(.degrees(-90))
                            Text("\(Int(payload.usagePercent * 100))%")
                                .font(.system(size: 9, weight: .bold))
                        }
                        .frame(width: 42, height: 42)

                        VStack(alignment: .leading, spacing: 1) {
                            Text("Key Remaining")
                                .font(.system(size: 9))
                                .foregroundStyle(.secondary)
                            Text(String(format: "$%.2f", payload.keyRemaining ?? 0.0))
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundStyle(.green)
                        }
                    }

                    // Linear bar
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(Color.secondary.opacity(0.2))
                            Capsule()
                                .fill(payload.usagePercent > 0.9 ? Color.red : Color.purple)
                                .frame(width: geo.size.width * CGFloat(payload.usagePercent))
                        }
                    }
                    .frame(height: 5)
                } else {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Key Spend")
                            .font(.system(size: 10))
                            .foregroundStyle(.secondary)
                        Text(String(format: "$%.4f", payload.keyUsage))
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                    }
                }

                HStack {
                    Text("Used: $\(String(format: "%.2f", payload.keyUsage))")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                    Spacer()
                    if let lim = payload.keyLimit {
                        Text("Limit: $\(String(format: "%.2f", lim))")
                            .font(.system(size: 9))
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Divider().opacity(0.3)

            // RIGHT COLUMN: Account Overview (Separated Section)
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Account Total")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button(intent: RefreshBalanceIntent()) {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 10, weight: .bold))
                    }
                    .buttonStyle(.plain)
                }

                Spacer()

                VStack(alignment: .leading, spacing: 1) {
                    Text("Available Balance")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                    Text(String(format: "$%.2f", payload.totalBalance))
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundStyle(.blue)
                }

                // Account burn gauge
                VStack(alignment: .leading, spacing: 2) {
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(Color.secondary.opacity(0.2))
                            Capsule()
                                .fill(Color.blue)
                                .frame(width: geo.size.width * CGFloat(payload.accountBurnPercent))
                        }
                    }
                    .frame(height: 4)

                    HStack {
                        Text("Used $\(String(format: "%.0f", payload.totalUsage))")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text("Total $\(String(format: "%.0f", payload.totalCredits))")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer()

                HStack {
                    Spacer()
                    Text("Updated \(payload.lastUpdated, style: .time)")
                        .font(.system(size: 8))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(8)
            .background(Color.blue.opacity(0.06))
            .cornerRadius(8)
            .frame(width: 140)
        }
        .padding(12)
        .containerBackground(for: .widget) {
            Color(nsColor: .windowBackgroundColor)
        }
    }
}
