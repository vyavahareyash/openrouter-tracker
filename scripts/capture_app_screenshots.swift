import AppKit
import Foundation
import SwiftUI

@MainActor
func renderPNG<V: View>(view: V, width: CGFloat, height: CGFloat, isDark: Bool, to url: URL) {
    let window = NSWindow(
        contentRect: NSRect(x: 0, y: 0, width: width, height: height),
        styleMask: [.borderless],
        backing: .buffered,
        defer: false
    )
    window.appearance = NSAppearance(named: isDark ? .darkAqua : .aqua)

    let hostingView = NSHostingView(rootView: view)
    hostingView.frame = NSRect(x: 0, y: 0, width: width, height: height)
    hostingView.appearance = NSAppearance(named: isDark ? .darkAqua : .aqua)
    window.contentView = hostingView
    window.layoutIfNeeded()

    // Spin runloop briefly so SwiftUI layout and splitview columns can expand and settle
    RunLoop.current.run(until: Date().addingTimeInterval(0.3))

    guard let bitmapRep = hostingView.bitmapImageRepForCachingDisplay(in: hostingView.bounds) else {
        fputs("Error: Failed to obtain bitmap image representation for app screenshot\n", stderr)
        return
    }
    bitmapRep.size = NSSize(width: width, height: height)
    bitmapRep.pixelsWide = Int(width * 2)
    bitmapRep.pixelsHigh = Int(height * 2)

    hostingView.cacheDisplay(in: hostingView.bounds, to: bitmapRep)

    if let pngData = bitmapRep.representation(using: .png, properties: [:]) {
        do {
            try pngData.write(to: url)
            print("📸 Captured App: \(url.lastPathComponent)")
        } catch {
            fputs("Error saving \(url.path): \(error)\n", stderr)
        }
    }
}

// macOS Application Window Card Wrapper with authentic window chrome
struct MacOSAppWindowContainer<Content: View>: View {
    let isDark: Bool
    let windowWidth: CGFloat
    let windowHeight: CGFloat
    @ViewBuilder let content: () -> Content

    var body: some View {
        VStack(spacing: 0) {
            // Window Title Bar
            HStack(spacing: 8) {
                // Traffic lights
                HStack(spacing: 7) {
                    Circle().fill(Color(red: 0.93, green: 0.42, blue: 0.37)).frame(width: 12, height: 12)
                    Circle().fill(Color(red: 0.96, green: 0.75, blue: 0.31)).frame(width: 12, height: 12)
                    Circle().fill(Color(red: 0.38, green: 0.77, blue: 0.33)).frame(width: 12, height: 12)
                }
                .padding(.leading, 14)

                Spacer()

                Text("OpenRouter Tracker")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(isDark ? Color.white.opacity(0.85) : Color.black.opacity(0.75))

                Spacer()

                // Balance traffic light spacing on right
                Color.clear.frame(width: 50, height: 12)
            }
            .frame(height: 38)
            .background(isDark ? Color(red: 0.16, green: 0.17, blue: 0.20) : Color(red: 0.93, green: 0.94, blue: 0.96))

            Divider()

            // Window Content
            content()
                .frame(width: windowWidth, height: windowHeight - 39)
        }
        .frame(width: windowWidth, height: windowHeight)
        .background(isDark ? Color(red: 0.12, green: 0.13, blue: 0.15) : Color(red: 0.97, green: 0.98, blue: 0.99))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .stroke(isDark ? Color.white.opacity(0.12) : Color.black.opacity(0.10), lineWidth: 1)
        )
        .shadow(color: Color.black.opacity(isDark ? 0.45 : 0.18), radius: 24, x: 0, y: 12)
        .padding(32)
        .background(
            LinearGradient(
                colors: isDark
                    ? [Color(red: 0.07, green: 0.08, blue: 0.12), Color(red: 0.10, green: 0.12, blue: 0.18)]
                    : [Color(red: 0.88, green: 0.90, blue: 0.94), Color(red: 0.82, green: 0.85, blue: 0.90)],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }
}

@main
struct CaptureAppScreenshots {
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

        let windowWidth: CGFloat = 1000
        let windowHeight: CGFloat = 650
        let canvasWidth: CGFloat = windowWidth + 64   // 1064
        let canvasHeight: CGFloat = windowHeight + 64 // 714

        await MainActor.run {
            // App Dark
            let appDark = MacOSAppWindowContainer(isDark: true, windowWidth: windowWidth, windowHeight: windowHeight) {
                ContentView(isPreview: true)
            }.environment(\.colorScheme, .dark)
            renderPNG(view: appDark, width: canvasWidth, height: canvasHeight, isDark: true, to: outDir.appendingPathComponent("app_dark.png"))

            // App Light
            let appLight = MacOSAppWindowContainer(isDark: false, windowWidth: windowWidth, windowHeight: windowHeight) {
                ContentView(isPreview: true)
            }.environment(\.colorScheme, .light)
            renderPNG(view: appLight, width: canvasWidth, height: canvasHeight, isDark: false, to: outDir.appendingPathComponent("app_light.png"))
        }

        print("✨ Saved app screenshots to \(outDir.path)")
    }
}
