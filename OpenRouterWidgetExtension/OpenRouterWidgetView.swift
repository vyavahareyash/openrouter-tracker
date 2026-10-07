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

// MARK: - Reusable Tactile Refresh Button
struct TactileRefreshButton: View {
    var body: some View {
        Button(intent: RefreshBalanceIntent()) {
            Image(systemName: "arrow.clockwise")
                .font(.system(size: 9, weight: .bold))
                .foregroundStyle(.secondary)
                .frame(width: 18, height: 18)
                .background(Color.secondary.opacity(0.12))
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Small Widget View (Square)
struct SmallWidgetView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(spacing: 8) {
            // Header: Nickname + Refresh Button
            HStack(spacing: 4) {
                Circle()
                    .fill(OpenRouterTheme.neonViolet)
                    .frame(width: 6, height: 6)
                Text(payload.customNickname)
                    .font(.system(size: 11, weight: .bold))
                    .lineLimit(1)
                    .truncationMode(.tail)
                Spacer(minLength: 2)
                TactileRefreshButton()
            }

            if let err = payload.errorMessage {
                Spacer()
                Text("⚠️ \(err)")
                    .font(.system(size: 9))
                    .foregroundStyle(.red)
                    .lineLimit(3)
                Spacer()
            } else {
                Spacer(minLength: 0)

                if let limit = payload.keyLimit, limit > 0 {
                    // Prominent Center Radial Ring Gauge
                    ZStack {
                        Circle()
                            .stroke(Color.secondary.opacity(0.18), lineWidth: 7.5)
                        Circle()
                            .trim(from: 0, to: CGFloat(payload.usagePercent))
                            .stroke(
                                payload.gaugeStrokeGradient,
                                style: StrokeStyle(lineWidth: 7.5, lineCap: .round)
                            )
                            .rotationEffect(.degrees(-90))

                        VStack(spacing: 1) {
                            Text("REMAINING")
                                .font(.system(size: 8, weight: .bold))
                                .foregroundStyle(.secondary)
                            Text(String(format: "$%.2f", payload.keyRemaining ?? 0.0))
                                .font(.system(size: 19, weight: .bold, design: .rounded))
                                .foregroundStyle(.green)
                                .lineLimit(1)
                                .minimumScaleFactor(0.7)
                            Text("\(Int(payload.usagePercent * 100))% USED")
                                .font(.system(size: 8, weight: .bold, design: .rounded))
                                .foregroundStyle(payload.usagePercent > 0.9 ? .red : (payload.usagePercent > 0.75 ? .orange : .secondary))
                        }
                    }
                    .frame(width: 96, height: 96)
                } else {
                    // Unlimited Spend View
                    VStack(spacing: 4) {
                        Image(systemName: "infinity.circle.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(Color(red: 0.66, green: 0.34, blue: 0.96))
                        Text("KEY SPEND")
                            .font(.system(size: 8, weight: .bold))
                            .foregroundStyle(.secondary)
                        Text(String(format: "$%.4f", payload.keyUsage))
                            .font(.system(size: 18, weight: .bold, design: .rounded))
                            .lineLimit(1)
                            .minimumScaleFactor(0.75)
                        Text("Unlimited")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer(minLength: 0)
            }
        }
        .padding(10)
        .containerBackground(for: .widget) {
            Color(nsColor: .windowBackgroundColor)
        }
    }
}

// MARK: - Medium Widget View (Rectangular)
struct MediumWidgetView: View {
    let payload: WidgetPayload

    var body: some View {
        HStack(spacing: 12) {
            // LEFT COLUMN: Key-Specific Metrics (Primary)
            VStack(alignment: .leading, spacing: 6) {
                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 5) {
                        Circle()
                            .fill(OpenRouterTheme.routerGradient)
                            .frame(width: 7, height: 7)
                        Text(payload.customNickname)
                            .font(.system(size: 11.5, weight: .bold))
                            .lineLimit(1)
                    }
                    Text(payload.keyMasked)
                        .font(.system(size: 8.5, design: .monospaced))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }

                Spacer(minLength: 0)

                if let limit = payload.keyLimit, limit > 0 {
                    HStack(spacing: 12) {
                        // Prominent Center Radial Ring Gauge (same as Small Widget)
                        ZStack {
                            Circle()
                                .stroke(Color.secondary.opacity(0.18), lineWidth: 7.0)
                            Circle()
                                .trim(from: 0, to: CGFloat(payload.usagePercent))
                                .stroke(
                                    payload.gaugeStrokeGradient,
                                    style: StrokeStyle(lineWidth: 7.0, lineCap: .round)
                                )
                                .rotationEffect(.degrees(-90))

                            VStack(spacing: 1) {
                                Text("REMAINING")
                                    .font(.system(size: 7.5, weight: .bold))
                                    .foregroundStyle(.secondary)
                                Text(String(format: "$%.2f", payload.keyRemaining ?? 0.0))
                                    .font(.system(size: 17, weight: .bold, design: .rounded))
                                    .foregroundStyle(.green)
                                    .lineLimit(1)
                                    .minimumScaleFactor(0.7)
                                Text("\(Int(payload.usagePercent * 100))% USED")
                                    .font(.system(size: 7.5, weight: .bold, design: .rounded))
                                    .foregroundStyle(payload.usagePercent > 0.9 ? .red : (payload.usagePercent > 0.75 ? .orange : .secondary))
                            }
                        }
                        .frame(width: 88, height: 88)

                        // Spend & Limit stats beside prominent gauge
                        VStack(alignment: .leading, spacing: 10) {
                            VStack(alignment: .leading, spacing: 1) {
                                Text("SPENT")
                                    .font(.system(size: 7.5, weight: .bold))
                                    .foregroundStyle(.secondary)
                                Text(String(format: "$%.2f", payload.keyUsage))
                                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                                    .foregroundStyle(OpenRouterTheme.neonViolet)
                            }
                            VStack(alignment: .leading, spacing: 1) {
                                Text("LIMIT")
                                    .font(.system(size: 7.5, weight: .bold))
                                    .foregroundStyle(.secondary)
                                Text(String(format: "$%.2f", limit))
                                    .font(.system(size: 13, weight: .bold, design: .monospaced))
                                    .foregroundStyle(OpenRouterTheme.amberWarning)
                            }
                        }
                    }
                } else {
                    // Unlimited Spend View
                    VStack(alignment: .leading, spacing: 4) {
                        HStack(spacing: 8) {
                            Image(systemName: "infinity.circle.fill")
                                .font(.system(size: 28))
                                .foregroundStyle(OpenRouterTheme.neonViolet)
                            VStack(alignment: .leading, spacing: 1) {
                                Text("KEY SPEND")
                                    .font(.system(size: 8, weight: .bold))
                                    .foregroundStyle(.secondary)
                                Text(String(format: "$%.4f", payload.keyUsage))
                                    .font(.system(size: 18, weight: .bold, design: .rounded))
                                    .lineLimit(1)
                                    .minimumScaleFactor(0.8)
                            }
                        }
                        Text("Unlimited Tier")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                    }
                }

                Spacer(minLength: 0)
            }

            Divider().opacity(0.3)

            // RIGHT COLUMN: Account Overview (Separated Section)
            VStack(alignment: .leading, spacing: 6) {
                HStack {
                    Text("Account Total")
                        .font(.system(size: 10, weight: .semibold))
                        .foregroundStyle(.secondary)
                    Spacer()
                    TactileRefreshButton()
                }

                Spacer()

                VStack(alignment: .leading, spacing: 1) {
                    Text("Available Balance")
                        .font(.system(size: 9))
                        .foregroundStyle(.secondary)
                    Text(String(format: "$%.2f", payload.totalBalance))
                        .font(.system(size: 18, weight: .bold, design: .rounded))
                        .foregroundStyle(.blue)
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
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
                            .lineLimit(1)
                        Spacer()
                        Text("Total $\(String(format: "%.0f", payload.totalCredits))")
                            .font(.system(size: 8))
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
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
