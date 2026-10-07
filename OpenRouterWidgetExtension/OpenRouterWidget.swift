import SwiftUI
import WidgetKit

struct OpenRouterTimelineEntry: TimelineEntry {
    let date: Date
    let payload: WidgetPayload
}

struct OpenRouterTimelineProvider: TimelineProvider {
    func placeholder(in context: Context) -> OpenRouterTimelineEntry {
        if let cached = SharedStorage.getPayload() {
            return OpenRouterTimelineEntry(date: Date(), payload: cached)
        }
        return OpenRouterTimelineEntry(date: Date(), payload: .placeholder)
    }

    func getSnapshot(in context: Context, completion: @escaping (OpenRouterTimelineEntry) -> Void) {
        if let cached = SharedStorage.getPayload() {
            completion(OpenRouterTimelineEntry(date: Date(), payload: cached))
        } else {
            completion(OpenRouterTimelineEntry(date: Date(), payload: .placeholder))
        }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<OpenRouterTimelineEntry>) -> Void) {
        Task {
            var payload = await OpenRouterService.refreshAndSave()

            // If refresh errored or returned empty, check if we have a valid cached payload
            if payload.errorMessage != nil, let cached = SharedStorage.getPayload(), cached.errorMessage == nil {
                payload = cached
            }

            let entry = OpenRouterTimelineEntry(date: Date(), payload: payload)

            // Auto-refresh timeline every 30 minutes
            let nextRefresh = Calendar.current.date(byAdding: .minute, value: 30, to: Date()) ?? Date().addingTimeInterval(1800)
            let timeline = Timeline(entries: [entry], policy: .after(nextRefresh))
            completion(timeline)
        }
    }
}

struct OpenRouterWidget: Widget {
    let kind: String = "OpenRouterWidget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: OpenRouterTimelineProvider()) { entry in
            OpenRouterWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("OpenRouter Balance")
        .description("Track OpenRouter balance, key usage, and credit limits with 1-click refresh.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}
