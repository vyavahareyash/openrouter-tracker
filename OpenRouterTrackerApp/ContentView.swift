import Charts
import SwiftUI
import WidgetKit

struct ContentView: View {
    var isPreview: Bool = false
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    @State private var keys: [TrackedKey] = []
    @State private var selectedKeyId: UUID?
    @State private var payloads: [UUID: WidgetPayload] = [:]
    @State private var isRefreshing: Bool = false
    @State private var showAddKeySheet: Bool = false
    @State private var statusMessage: String = ""

    // Editing nickname
    @State private var isEditingLabel: Bool = false
    @State private var editedLabel: String = ""

    private var selectedKey: TrackedKey? {
        keys.first(where: { $0.id == selectedKeyId }) ?? keys.first
    }

    private var activePayload: WidgetPayload? {
        guard let key = selectedKey else { return nil }
        return payloads[key.id] ?? SharedStorage.getPayload(for: key.id)
    }

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            // MARK: - Sidebar: Keys List
            List {
                Section("Tracked Keys") {
                    ForEach(keys) { key in
                        Button(action: { selectedKeyId = key.id }) {
                            KeyRowView(
                                key: key,
                                payload: payloads[key.id] ?? SharedStorage.getPayload(for: key.id),
                                isSelected: key.id == selectedKey?.id
                            )
                        }
                        .buttonStyle(.plain)
                        .listRowInsets(EdgeInsets(top: 2, leading: 6, bottom: 2, trailing: 6))
                        .listRowSeparator(.hidden)
                    }
                }
            }
            .listStyle(.sidebar)
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: 8) {
                    Divider()
                    Button(action: { showAddKeySheet = true }) {
                        HStack(spacing: 8) {
                            Image(systemName: "plus.circle.fill")
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundStyle(OpenRouterTheme.electricBlue)
                            Text("Add API Key")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundStyle(Color.primary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(Color.secondary.opacity(0.08))
                        .cornerRadius(6)
                    }
                    .buttonStyle(.plain)
                    .padding(.horizontal, 12)
                    .padding(.bottom, 8)
                }
                .background(Color(nsColor: .windowBackgroundColor))
            }
            .navigationSplitViewColumnWidth(min: 240, ideal: 280, max: 340)
        } detail: {
            // MARK: - Detail: Active Key Metrics & Visuals
            if let key = selectedKey {
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        // Key Header Card
                        KeyHeaderView(
                            key: key,
                            isEditing: $isEditingLabel,
                            editedLabel: $editedLabel,
                            onSaveLabel: saveEditedLabel,
                            onToggleWidget: { toggleWidgetKey(key.id) },
                            onRefresh: { refreshKey(key) },
                            onDelete: { deleteKey(key.id) },
                            isRefreshing: isRefreshing
                        )

                        if let payload = activePayload {
                            // Error banner if any
                            if let err = payload.errorMessage {
                                Text("⚠️ \(err)")
                                    .font(.footnote)
                                    .foregroundStyle(.red)
                                    .padding(8)
                                    .background(Color.red.opacity(0.1))
                                    .cornerRadius(6)
                            }

                            // 1. PRIMARY SECTION: Key-Specific Budget & Visuals
                            KeyBudgetSectionView(payload: payload)

                            // 2. SECONDARY SECTION: Account Overview (Separated)
                            AccountOverviewSectionView(payload: payload)
                        } else {
                            ProgressView("Loading key metrics...")
                                .frame(maxWidth: .infinity, alignment: .center)
                                .padding(40)
                        }
                    }
                    .padding(24)
                }
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "key.fill")
                        .font(.system(size: 40))
                        .foregroundStyle(.secondary)
                    Text("No API Keys Added")
                        .font(.headline)
                    Button("Add Your First Key") {
                        showAddKeySheet = true
                    }
                    .buttonStyle(.borderedProminent)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .frame(minWidth: 780, minHeight: 540)
        .sheet(isPresented: $showAddKeySheet) {
            AddKeySheetView(onAdd: handleAddKey)
        }
        .onAppear {
            loadInitialData()
        }
    }

    // MARK: - Actions

    private func loadInitialData() {
        if isPreview {
            keys = MockData.sampleKeys
            selectedKeyId = MockData.primaryKeyId
            payloads = MockData.samplePayloads
            return
        }
        keys = SharedStorage.loadAllKeys()
        if let widgetKey = keys.first(where: { $0.isWidgetKey }) ?? keys.first {
            selectedKeyId = widgetKey.id
        }
        for k in keys {
            if let p = SharedStorage.getPayload(for: k.id) {
                payloads[k.id] = p
            }
        }
        if let sel = selectedKey {
            refreshKey(sel)
        }
    }

    private func handleAddKey(label: String, apiKey: String, isWidget: Bool) {
        let newKey = SharedStorage.addKey(customLabel: label, apiKey: apiKey, isWidgetKey: isWidget)
        keys = SharedStorage.loadAllKeys()
        selectedKeyId = newKey.id
        refreshKey(newKey)
    }

    private func saveEditedLabel() {
        guard var key = selectedKey, !editedLabel.isEmpty else { return }
        key.customLabel = editedLabel
        SharedStorage.updateKey(key)
        keys = SharedStorage.loadAllKeys()
        isEditingLabel = false

        // Update cached payload
        if var p = payloads[key.id] {
            p.customNickname = editedLabel
            payloads[key.id] = p
            SharedStorage.savePayload(p, for: key.id)
            if key.isWidgetKey {
                SharedStorage.saveWidgetPayload(p)
                WidgetCenter.shared.reloadAllTimelines()
            }
        }
    }

    private func toggleWidgetKey(_ id: UUID) {
        SharedStorage.setWidgetKey(id: id)
        keys = SharedStorage.loadAllKeys()
        WidgetCenter.shared.reloadAllTimelines()
    }

    private func deleteKey(_ id: UUID) {
        SharedStorage.deleteKey(id: id)
        keys = SharedStorage.loadAllKeys()
        payloads.removeValue(forKey: id)
        selectedKeyId = keys.first?.id
        WidgetCenter.shared.reloadAllTimelines()
    }

    private func refreshKey(_ key: TrackedKey) {
        isRefreshing = true
        Task {
            let p = await OpenRouterService.refreshKey(key)
            await MainActor.run {
                payloads[key.id] = p
                isRefreshing = false
                if key.isWidgetKey {
                    WidgetCenter.shared.reloadAllTimelines()
                }
            }
        }
    }
}

// MARK: - Sidebar Row
struct KeyRowView: View {
    @Environment(\.colorScheme) private var colorScheme
    let key: TrackedKey
    let payload: WidgetPayload?
    let isSelected: Bool

    var body: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(key.isWidgetKey ? OpenRouterTheme.electricBlue : (isSelected ? Color.white.opacity(0.85) : (colorScheme == .dark ? Color.white.opacity(0.35) : Color.secondary.opacity(0.4))))
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 4) {
                    Text(key.customLabel)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(isSelected ? Color.white : (colorScheme == .dark ? Color.white.opacity(0.9) : Color.primary))
                        .lineLimit(1)
                    if key.isWidgetKey {
                        Image(systemName: "widget.small")
                            .font(.system(size: 10))
                            .foregroundStyle(isSelected ? Color.white : OpenRouterTheme.electricBlue)
                    }
                }

                Text(key.keyMasked)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(isSelected ? Color.white.opacity(0.75) : (colorScheme == .dark ? Color.white.opacity(0.55) : Color.secondary))
            }

            Spacer()

            if let p = payload, let limit = p.keyLimit, limit > 0 {
                Text("\(Int(p.usagePercent * 100))%")
                    .font(.system(size: 11, weight: .bold, design: .rounded))
                    .foregroundStyle(isSelected ? Color.white : (p.usagePercent > 0.9 ? OpenRouterTheme.coralRed : (p.usagePercent > 0.75 ? OpenRouterTheme.amberWarning : OpenRouterTheme.neonViolet)))
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(isSelected ? Color.white.opacity(0.2) : (colorScheme == .dark ? Color.white.opacity(0.12) : Color.secondary.opacity(0.12)))
                    .cornerRadius(4)
            }
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(
            RoundedRectangle(cornerRadius: 8, style: .continuous)
                .fill(isSelected ? OpenRouterTheme.electricBlue : Color.clear)
        )
    }
}

// MARK: - Key Header View
struct KeyHeaderView: View {
    let key: TrackedKey
    @Binding var isEditing: Bool
    @Binding var editedLabel: String
    let onSaveLabel: () -> Void
    let onToggleWidget: () -> Void
    let onRefresh: () -> Void
    let onDelete: () -> Void
    let isRefreshing: Bool

    @State private var showDeleteConfirm: Bool = false

    var body: some View {
        HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 4) {
                if isEditing {
                    HStack {
                        TextField("Nickname", text: $editedLabel)
                            .textFieldStyle(.roundedBorder)
                            .frame(maxWidth: 220)
                        Button("Save", action: onSaveLabel)
                        Button("Cancel") { isEditing = false }
                    }
                } else {
                    HStack(spacing: 8) {
                        Text(key.customLabel)
                            .font(.title2.bold())
                        Button(action: {
                            editedLabel = key.customLabel
                            isEditing = true
                        }) {
                            Image(systemName: "pencil")
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                }

                HStack(spacing: 8) {
                    Text("Token: \(key.keyMasked)")
                        .font(.system(size: 11, design: .monospaced))
                        .foregroundStyle(.secondary)
                    if key.isWidgetKey {
                        Label("Active on Desktop Widget", systemImage: "checkmark.seal.fill")
                            .font(.caption2.bold())
                            .foregroundStyle(OpenRouterTheme.electricBlue)
                    }
                }
            }

            Spacer()

            HStack(spacing: 10) {
                Button(action: onToggleWidget) {
                    Label(
                        key.isWidgetKey ? "Pinned to Widget" : "Pin to Widget",
                        systemImage: key.isWidgetKey ? "pin.fill" : "pin"
                    )
                }
                .buttonStyle(.bordered)
                .tint(key.isWidgetKey ? OpenRouterTheme.electricBlue : .secondary)

                Button(action: onRefresh) {
                    if isRefreshing {
                        ProgressView().scaleEffect(0.6)
                    } else {
                        Image(systemName: "arrow.clockwise")
                    }
                }
                .disabled(isRefreshing)

                Button(role: .destructive, action: { showDeleteConfirm = true }) {
                    Image(systemName: "trash")
                }
                .tint(.red)
                .confirmationDialog("Delete '\(key.customLabel)'?", isPresented: $showDeleteConfirm) {
                    Button("Delete Key", role: .destructive, action: onDelete)
                    Button("Cancel", role: .cancel) {}
                } message: {
                    Text("This key and its metrics will be permanently removed.")
                }
            }
        }
        .padding(.bottom, 8)
    }
}

// MARK: - 1. Key-Specific Budget & Visuals
struct KeyBudgetSectionView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Label("Key Budget & Usage", systemImage: "chart.donut")
                    .font(.headline)
                Spacer()
                Text("Updated \(payload.lastUpdated.formatted(date: .omitted, time: .standard))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            // Visual Gauge Row
            HStack(spacing: 24) {
                // Donut Visual
                if let limit = payload.keyLimit, limit > 0 {
                    ZStack {
                        Circle()
                            .stroke(Color.secondary.opacity(0.15), lineWidth: 14)
                        Circle()
                            .trim(from: 0, to: CGFloat(payload.usagePercent))
                            .stroke(
                                payload.gaugeStrokeGradient,
                                style: StrokeStyle(lineWidth: 14, lineCap: .round)
                            )
                            .rotationEffect(.degrees(-90))

                        VStack(spacing: 0) {
                            Text("\(Int(payload.usagePercent * 100))%")
                                .font(.system(size: 22, weight: .bold, design: .rounded))
                            Text("USED")
                                .font(.system(size: 9, weight: .semibold))
                                .foregroundStyle(.secondary)
                        }
                    }
                    .frame(width: 100, height: 100)
                }

                // Numbers Grid
                VStack(alignment: .leading, spacing: 8) {
                    HStack(spacing: 20) {
                        BudgetStatCard(
                            title: "Key Spend",
                            value: String(format: "$%.4f", payload.keyUsage),
                            subtitle: "USD",
                            color: OpenRouterTheme.neonViolet
                        )

                        if let rem = payload.keyRemaining {
                            BudgetStatCard(
                                title: "Remaining Budget",
                                value: String(format: "$%.4f", rem),
                                subtitle: "USD",
                                color: OpenRouterTheme.emeraldGreen
                            )
                        }

                        BudgetStatCard(
                            title: "Assigned Limit",
                            value: payload.keyLimit != nil ? String(format: "$%.2f", payload.keyLimit!) : "Unlimited",
                            subtitle: "USD",
                            color: OpenRouterTheme.amberWarning
                        )
                    }


                }
            }
            .padding()
            .background(Color(nsColor: .controlBackgroundColor))
            .cornerRadius(12)

            // Periodic Spend Breakdown Pills
            HStack(spacing: 12) {
                PeriodCard(label: "Today's Spend", value: payload.usageDaily)
                PeriodCard(label: "This Week", value: payload.usageWeekly)
                PeriodCard(label: "This Month", value: payload.usageMonthly)
            }
        }
    }
}

// MARK: - 2. Account Overview Section (Separated)
struct AccountOverviewSectionView: View {
    let payload: WidgetPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("Account Overview (Shared Balance)", systemImage: "building.columns")
                .font(.headline)
                .foregroundStyle(.secondary)

            VStack(alignment: .leading, spacing: 14) {
                HStack(spacing: 24) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Available Account Balance")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                        Text(String(format: "$%.2f", payload.totalBalance))
                            .font(.system(size: 28, weight: .bold, design: .rounded))
                            .foregroundStyle(OpenRouterTheme.electricBlue)
                    }

                    Spacer()

                    HStack(spacing: 20) {
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("Total Purchased")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(String(format: "$%.2f", payload.totalCredits))
                                .font(.system(size: 15, weight: .semibold, design: .monospaced))
                        }
                        VStack(alignment: .trailing, spacing: 2) {
                            Text("Account Burn")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text(String(format: "$%.2f", payload.totalUsage))
                                .font(.system(size: 15, weight: .semibold, design: .monospaced))
                        }
                    }
                }

                // Account Burn Bar
                VStack(alignment: .leading, spacing: 4) {
                    GeometryReader { geo in
                        ZStack(alignment: .leading) {
                            Capsule()
                                .fill(Color.secondary.opacity(0.15))
                            Capsule()
                                .fill(OpenRouterTheme.electricBlue)
                                .frame(width: geo.size.width * CGFloat(payload.accountBurnPercent))
                        }
                    }
                    .frame(height: 6)

                    HStack {
                        Text("Total used: $\(String(format: "%.2f", payload.totalUsage)) (\(Int(payload.accountBurnPercent * 100))%)")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text("Credits pool: $\(String(format: "%.2f", payload.totalCredits))")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .padding(16)
            .background(OpenRouterTheme.electricBlue.opacity(0.06))
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(OpenRouterTheme.electricBlue.opacity(0.18), lineWidth: 1)
            )
            .cornerRadius(12)
        }
    }
}

// MARK: - Reusable Cards
struct BudgetStatCard: View {
    let title: String
    let value: String
    let subtitle: String
    let color: Color

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundStyle(color)
            Text(subtitle)
                .font(.system(size: 9))
                .foregroundStyle(.tertiary)
        }
        .frame(minWidth: 100, alignment: .leading)
    }
}

struct PeriodCard: View {
    let label: String
    let value: Double?

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(label)
                .font(.caption2)
                .foregroundStyle(.secondary)
            if let v = value {
                Text(String(format: "$%.4f", v))
                    .font(.system(size: 13, weight: .semibold, design: .monospaced))
            } else {
                Text("—")
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(nsColor: .controlBackgroundColor))
        .cornerRadius(8)
    }
}

// MARK: - Add Key Sheet
struct AddKeySheetView: View {
    @Environment(\.dismiss) var dismiss
    @State private var label: String = ""
    @State private var apiKey: String = ""
    @State private var isWidget: Bool = false
    @State private var isTesting: Bool = false
    @State private var errorMessage: String = ""

    let onAdd: (String, String, Bool) -> Void

    var body: some View {
        VStack(spacing: 20) {
            Text("Add New OpenRouter Key")
                .font(.headline)

            VStack(alignment: .leading, spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Custom Nickname")
                        .font(.caption.bold())
                    TextField("e.g. Work Backend, Personal Project", text: $label)
                        .textFieldStyle(.roundedBorder)
                }

                VStack(alignment: .leading, spacing: 4) {
                    Text("API Key")
                        .font(.caption.bold())
                    SecureField("sk-or-v1-...", text: $apiKey)
                        .textFieldStyle(.roundedBorder)
                }

                Toggle("Pin to Desktop Widget", isOn: $isWidget)
                    .font(.subheadline)

                if !errorMessage.isEmpty {
                    Text("❌ \(errorMessage)")
                        .font(.footnote)
                        .foregroundStyle(.red)
                }
            }

            HStack {
                Button("Cancel") { dismiss() }
                    .keyboardShortcut(.cancelAction)

                Spacer()

                Button("Save Key") {
                    testAndSave()
                }
                .keyboardShortcut(.defaultAction)
                .disabled(apiKey.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isTesting)
            }
        }
        .padding(24)
        .frame(width: 440)
    }

    private func testAndSave() {
        let cleanKey = apiKey.trimmingCharacters(in: .whitespacesAndNewlines)
        isTesting = true
        errorMessage = ""

        Task {
            let payload = await OpenRouterService.fetchData(apiKey: cleanKey, customNickname: label)
            await MainActor.run {
                isTesting = false
                if let err = payload.errorMessage {
                    errorMessage = err
                } else {
                    onAdd(label, cleanKey, isWidget)
                    dismiss()
                }
            }
        }
    }
}
