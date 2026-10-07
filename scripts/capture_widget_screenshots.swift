import AppKit
import AppIntents
import Foundation
import SwiftUI
import WidgetKit

@MainActor
func renderPNG<V: View>(view: V, width: CGFloat, height: CGFloat, isDark: Bool, to url: URL) {
    let hostingView = NSHostingView(rootView: view)
    hostingView.frame = NSRect(x: 0, y: 0, width: width, height: height)
    hostingView.appearance = NSAppearance(named: isDark ? .darkAqua : .aqua)

    guard let bitmapRep = hostingView.bitmapImageRepForCachingDisplay(in: hostingView.bounds) else {
        fputs("Error: Failed to obtain bitmap image representation\n", stderr)
        return
    }
    bitmapRep.size = NSSize(width: width, height: height)
    bitmapRep.pixelsWide = Int(width * 2)
    bitmapRep.pixelsHigh = Int(height * 2)

    hostingView.cacheDisplay(in: hostingView.bounds, to: bitmapRep)

    if let pngData = bitmapRep.representation(using: .png, properties: [:]) {
        do {
            try pngData.write(to: url)
            print("📸 Captured: \(url.lastPathComponent)")
        } catch {
            fputs("Error saving \(url.path): \(error)\n", stderr)
        }
    }
}

// macOS Widget Card Wrapper with authentic desktop wallpaper and squircle frame
struct MacOSWidgetContainer<Content: View>: View {
    let isDark: Bool
    let width: CGFloat
    let height: CGFloat
    @ViewBuilder let content: () -> Content

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(isDark ? Color(red: 0.12, green: 0.13, blue: 0.16) : Color(red: 0.95, green: 0.96, blue: 0.98))
                .shadow(color: Color.black.opacity(isDark ? 0.35 : 0.12), radius: 10, x: 0, y: 4)

            content()
        }
        .frame(width: width, height: height)
        .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(isDark ? Color.white.opacity(0.12) : Color.black.opacity(0.08), lineWidth: 1)
        )
        .padding(16)
        .background(
            LinearGradient(
                colors: isDark
                    ? [Color(red: 0.06, green: 0.08, blue: 0.12), Color(red: 0.09, green: 0.11, blue: 0.18)]
                    : [Color(red: 0.88, green: 0.90, blue: 0.94), Color(red: 0.82, green: 0.85, blue: 0.90)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }
}

@main
struct CaptureWidgetScreenshots {
    static func main() async {
        let args = CommandLine.arguments
        let targetDirStr = args.count > 1 ? args[1] : "./screenshots"
        let outDir = URL(fileURLWithPath: targetDirStr)

        do {
            try FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
        } catch {
            fputs("Failed to create target directory \(targetDirStr): \(error)\n", stderr)
            exit(1)
        }

        // Use rich dummy data from MockData for crisp, consistent showcases
        let payload = MockData.defaultWidgetPayload

        await MainActor.run {
            // Small Dark (Canvas size = 170+32 = 202)
            let sDark = MacOSWidgetContainer(isDark: true, width: 170, height: 170) {
                SmallWidgetView(payload: payload)
            }.environment(\.colorScheme, .dark)
            renderPNG(view: sDark, width: 202, height: 202, isDark: true, to: outDir.appendingPathComponent("widget_small_dark.png"))

            // Small Light
            let sLight = MacOSWidgetContainer(isDark: false, width: 170, height: 170) {
                SmallWidgetView(payload: payload)
            }.environment(\.colorScheme, .light)
            renderPNG(view: sLight, width: 202, height: 202, isDark: false, to: outDir.appendingPathComponent("widget_small_light.png"))

            // Medium Dark (Canvas size = 364+32 = 396 x 202)
            let mDark = MacOSWidgetContainer(isDark: true, width: 364, height: 170) {
                MediumWidgetView(payload: payload)
            }.environment(\.colorScheme, .dark)
            renderPNG(view: mDark, width: 396, height: 202, isDark: true, to: outDir.appendingPathComponent("widget_medium_dark.png"))

            // Medium Light
            let mLight = MacOSWidgetContainer(isDark: false, width: 364, height: 170) {
                MediumWidgetView(payload: payload)
            }.environment(\.colorScheme, .light)
            renderPNG(view: mLight, width: 396, height: 202, isDark: false, to: outDir.appendingPathComponent("widget_medium_light.png"))
        }

        print("✨ Saved all screenshots to \(outDir.path)")
    }
}
