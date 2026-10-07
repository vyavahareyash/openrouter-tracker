import Cocoa

let width: CGFloat = 1200
let height: CGFloat = 280
let scale: CGFloat = 2.0 // Retina

let imgSize = NSSize(width: width, height: height)
let pixelWidth = Int(width * scale)
let pixelHeight = Int(height * scale)

guard let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil,
    pixelsWide: pixelWidth,
    pixelsHigh: pixelHeight,
    bitsPerSample: 8,
    samplesPerPixel: 4,
    hasAlpha: true,
    isPlanar: false,
    colorSpaceName: .deviceRGB,
    bytesPerRow: 0,
    bitsPerPixel: 0
) else {
    fatalError("Failed to create bitmap rep")
}
rep.size = imgSize

NSGraphicsContext.saveGraphicsState()
guard let ctx = NSGraphicsContext(bitmapImageRep: rep) else {
    fatalError("Failed to create graphics context")
}
NSGraphicsContext.current = ctx
let cgContext = ctx.cgContext

// 1. Deep modern gradient background
let colors = [
    NSColor(calibratedRed: 0.08, green: 0.10, blue: 0.16, alpha: 1.0).cgColor,
    NSColor(calibratedRed: 0.03, green: 0.04, blue: 0.07, alpha: 1.0).cgColor
] as CFArray
let colorSpace = CGColorSpaceCreateDeviceRGB()
if let gradient = CGGradient(colorsSpace: colorSpace, colors: colors, locations: [0.0, 1.0]) {
    cgContext.drawLinearGradient(gradient, start: CGPoint(x: 0, y: height), end: CGPoint(x: width, y: 0), options: [])
}

// 2. Ambient radial glows
func drawGlow(at center: CGPoint, color: NSColor, radius: CGFloat) {
    let glowColors = [
        color.withAlphaComponent(0.25).cgColor,
        color.withAlphaComponent(0.0).cgColor
    ] as CFArray
    if let glowGradient = CGGradient(colorsSpace: colorSpace, colors: glowColors, locations: [0.0, 1.0]) {
        cgContext.drawRadialGradient(glowGradient, startCenter: center, startRadius: 0, endCenter: center, endRadius: radius, options: [])
    }
}

drawGlow(at: CGPoint(x: 240, y: 140), color: NSColor(calibratedRed: 0.25, green: 0.50, blue: 1.0, alpha: 1.0), radius: 240)
drawGlow(at: CGPoint(x: 950, y: 140), color: NSColor(calibratedRed: 0.0, green: 0.85, blue: 0.80, alpha: 1.0), radius: 240)

// 3. Draw App Icon on left if available (macOS squircle shape)
let iconPath = "OpenRouterTrackerApp/AppIcon.png"
if let iconImage = NSImage(contentsOfFile: iconPath) {
    let iconRect = CGRect(x: 80, y: height - 175, width: 110, height: 110)
    let cornerRadius: CGFloat = 24.5
    let squirclePath = CGPath(roundedRect: iconRect, cornerWidth: cornerRadius, cornerHeight: cornerRadius, transform: nil)
    
    // 3a. Native macOS squircle drop shadow
    cgContext.saveGState()
    cgContext.setShadow(
        offset: CGSize(width: 0, height: -6),
        blur: 16,
        color: NSColor.black.withAlphaComponent(0.45).cgColor
    )
    cgContext.addPath(squirclePath)
    cgContext.setFillColor(NSColor.black.cgColor)
    cgContext.fillPath()
    cgContext.restoreGState()
    
    // 3b. Clipped app icon
    cgContext.saveGState()
    cgContext.addPath(squirclePath)
    cgContext.clip()
    iconImage.draw(in: iconRect)
    cgContext.restoreGState()
    
    // 3c. Subtle macOS icon border
    cgContext.saveGState()
    let strokePath = CGPath(roundedRect: iconRect.insetBy(dx: 0.5, dy: 0.5), cornerWidth: cornerRadius - 0.5, cornerHeight: cornerRadius - 0.5, transform: nil)
    cgContext.addPath(strokePath)
    cgContext.setStrokeColor(NSColor(white: 1.0, alpha: 0.18).cgColor)
    cgContext.setLineWidth(1.0)
    cgContext.strokePath()
    cgContext.restoreGState()
}

// 4. Headline & Subheading
let title = "OpenRouter Tracker"
let titleFont = NSFont.systemFont(ofSize: 42, weight: .heavy)
let titleAttrs: [NSAttributedString.Key: Any] = [
    .font: titleFont,
    .foregroundColor: NSColor.white
]
(title as NSString).draw(at: CGPoint(x: 215, y: height - 122), withAttributes: titleAttrs)

let tagText = "NATIVE MACOS DESKTOP WIDGET"
let tagAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 13, weight: .bold),
    .foregroundColor: NSColor(calibratedRed: 0.35, green: 0.75, blue: 1.0, alpha: 1.0)
]
(tagText as NSString).draw(at: CGPoint(x: 218, y: height - 72), withAttributes: tagAttrs)

let subtitle = "Real-time balance, credit usage & rate limits on your Mac Desktop with 1-click refresh."
let subFont = NSFont.systemFont(ofSize: 17, weight: .medium)
let subAttrs: [NSAttributedString.Key: Any] = [
    .font: subFont,
    .foregroundColor: NSColor(calibratedWhite: 0.72, alpha: 1.0)
]
(subtitle as NSString).draw(at: CGPoint(x: 218, y: height - 156), withAttributes: subAttrs)

// 5. Feature Badges / Pills
let pillItems = [
    ("⚡ 1-Click Interactive Refresh", NSColor(calibratedRed: 0.18, green: 0.32, blue: 0.55, alpha: 0.7)),
    ("🔋 Zero Background Daemon", NSColor(calibratedRed: 0.14, green: 0.38, blue: 0.32, alpha: 0.7)),
    ("🔐 Hardware Keychain Security", NSColor(calibratedRed: 0.35, green: 0.22, blue: 0.50, alpha: 0.7)),
    ("📦 100% Offline & Private", NSColor(calibratedRed: 0.22, green: 0.25, blue: 0.35, alpha: 0.7))
]

var pillX: CGFloat = 80
let pillY: CGFloat = height - 225
let pillHeight: CGFloat = 34

for (label, bgColor) in pillItems {
    let font = NSFont.systemFont(ofSize: 13, weight: .semibold)
    let textAttrs: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor.white
    ]
    let textSize = (label as NSString).size(withAttributes: textAttrs)
    let pillWidth = textSize.width + 28
    
    let rect = CGRect(x: pillX, y: pillY, width: pillWidth, height: pillHeight)
    let path = CGPath(roundedRect: rect, cornerWidth: 8, cornerHeight: 8, transform: nil)
    
    cgContext.setFillColor(bgColor.cgColor)
    cgContext.addPath(path)
    cgContext.fillPath()
    
    cgContext.setStrokeColor(NSColor(white: 1.0, alpha: 0.15).cgColor)
    cgContext.setLineWidth(1.0)
    cgContext.addPath(path)
    cgContext.strokePath()
    
    (label as NSString).draw(at: CGPoint(x: pillX + 14, y: pillY + 8), withAttributes: textAttrs)
    pillX += pillWidth + 14
}

NSGraphicsContext.restoreGraphicsState()

guard let pngData = rep.representation(using: .png, properties: [:]) else {
    fatalError("Failed to convert image to PNG")
}

let outputPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "assets/banner.png"
try pngData.write(to: URL(fileURLWithPath: outputPath))
print("Successfully generated banner at \(outputPath)")
