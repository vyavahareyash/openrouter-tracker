import Cocoa

let width: CGFloat = 660
let height: CGFloat = 420
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

// Note: NSGraphicsContext default has origin at bottom-left
// We can use native Cocoa drawing or CoreGraphics

// 1. Background gradient (sleek dark aesthetic)
let colors = [
    NSColor(calibratedRed: 0.12, green: 0.12, blue: 0.15, alpha: 1.0).cgColor,
    NSColor(calibratedRed: 0.07, green: 0.07, blue: 0.09, alpha: 1.0).cgColor
] as CFArray
let colorSpace = CGColorSpaceCreateDeviceRGB()
if let gradient = CGGradient(colorsSpace: colorSpace, colors: colors, locations: [0.0, 1.0]) {
    cgContext.drawLinearGradient(gradient, start: CGPoint(x: 0, y: height), end: CGPoint(x: 0, y: 0), options: [])
}

// 2. Subtle top highlight border
let topBorderPath = CGMutablePath()
topBorderPath.move(to: CGPoint(x: 0, y: height - 1))
topBorderPath.addLine(to: CGPoint(x: width, y: height - 1))
cgContext.setStrokeColor(NSColor(white: 1.0, alpha: 0.08).cgColor)
cgContext.setLineWidth(1.0)
cgContext.addPath(topBorderPath)
cgContext.strokePath()

// 3. Ambient soft glows behind the drop zones
// Left icon center in Finder: (180, 210) from top-left -> (180, height - 210 = 210) from bottom-left
let leftCenter = CGPoint(x: 180, y: 210)
let rightCenter = CGPoint(x: 480, y: 210)

func drawGlow(at center: CGPoint, color: NSColor, radius: CGFloat) {
    let glowColors = [
        color.withAlphaComponent(0.18).cgColor,
        color.withAlphaComponent(0.0).cgColor
    ] as CFArray
    if let glowGradient = CGGradient(colorsSpace: colorSpace, colors: glowColors, locations: [0.0, 1.0]) {
        cgContext.drawRadialGradient(glowGradient, startCenter: center, startRadius: 0, endCenter: center, endRadius: radius, options: [])
    }
}

drawGlow(at: leftCenter, color: NSColor(red: 0.38, green: 0.40, blue: 0.95, alpha: 1.0), radius: 110)
drawGlow(at: rightCenter, color: NSColor(red: 0.20, green: 0.70, blue: 0.95, alpha: 1.0), radius: 110)

// 4. Pedestal plates for the icons
func drawPedestal(at center: CGPoint) {
    let plateRect = CGRect(x: center.x - 70, y: center.y - 70, width: 140, height: 140)
    let path = CGPath(roundedRect: plateRect, cornerWidth: 28, cornerHeight: 28, transform: nil)
    
    // Fill
    cgContext.setFillColor(NSColor(white: 1.0, alpha: 0.03).cgColor)
    cgContext.addPath(path)
    cgContext.fillPath()
    
    // Border
    cgContext.setStrokeColor(NSColor(white: 1.0, alpha: 0.08).cgColor)
    cgContext.setLineWidth(1.5)
    cgContext.addPath(path)
    cgContext.strokePath()
}

drawPedestal(at: leftCenter)
drawPedestal(at: rightCenter)

// 5. Connecting arrow from Left to Right
let arrowY: CGFloat = 210
let arrowStartX: CGFloat = 265
let arrowEndX: CGFloat = 395

// Gradient line
let linePath = CGMutablePath()
linePath.move(to: CGPoint(x: arrowStartX, y: arrowY))
linePath.addLine(to: CGPoint(x: arrowEndX - 10, y: arrowY))

cgContext.setStrokeColor(NSColor(calibratedRed: 0.45, green: 0.50, blue: 0.95, alpha: 0.6).cgColor)
cgContext.setLineWidth(3.0)
cgContext.setLineCap(.round)
cgContext.addPath(linePath)
cgContext.strokePath()

// Arrow head
let headPath = CGMutablePath()
headPath.move(to: CGPoint(x: arrowEndX - 12, y: arrowY + 9))
headPath.addLine(to: CGPoint(x: arrowEndX, y: arrowY))
headPath.addLine(to: CGPoint(x: arrowEndX - 12, y: arrowY - 9))

cgContext.setStrokeColor(NSColor(calibratedRed: 0.45, green: 0.50, blue: 0.95, alpha: 0.9).cgColor)
cgContext.setLineWidth(3.0)
cgContext.setLineCap(.round)
cgContext.setLineJoin(.round)
cgContext.addPath(headPath)
cgContext.strokePath()

// Pill badge in the middle of arrow
let badgeWidth: CGFloat = 76
let badgeHeight: CGFloat = 22
let badgeRect = CGRect(x: (arrowStartX + arrowEndX - badgeWidth) / 2, y: arrowY - (badgeHeight / 2), width: badgeWidth, height: badgeHeight)
let badgePath = CGPath(roundedRect: badgeRect, cornerWidth: 11, cornerHeight: 11, transform: nil)

cgContext.setFillColor(NSColor(calibratedRed: 0.16, green: 0.17, blue: 0.22, alpha: 0.95).cgColor)
cgContext.addPath(badgePath)
cgContext.fillPath()

cgContext.setStrokeColor(NSColor(calibratedRed: 0.45, green: 0.50, blue: 0.95, alpha: 0.4).cgColor)
cgContext.setLineWidth(1.0)
cgContext.addPath(badgePath)
cgContext.strokePath()

let dragText = "INSTALL"
let dragTextAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 9.5, weight: .bold),
    .foregroundColor: NSColor(calibratedRed: 0.70, green: 0.75, blue: 1.0, alpha: 0.9)
]
let dragTextSize = (dragText as NSString).size(withAttributes: dragTextAttrs)
let dragTextPoint = CGPoint(
    x: badgeRect.midX - dragTextSize.width / 2,
    y: badgeRect.midY - dragTextSize.height / 2
)
(dragText as NSString).draw(at: dragTextPoint, withAttributes: dragTextAttrs)

// 6. Header Typography
let title = "OpenRouter Tracker"
let titleFont = NSFont.systemFont(ofSize: 22, weight: .bold)
let titleAttrs: [NSAttributedString.Key: Any] = [
    .font: titleFont,
    .foregroundColor: NSColor.white
]
let titleSize = (title as NSString).size(withAttributes: titleAttrs)
let titlePoint = CGPoint(x: (width - titleSize.width) / 2, y: height - 60)
(title as NSString).draw(at: titlePoint, withAttributes: titleAttrs)

let subtitle = "Drag OpenRouter Tracker to the Applications folder"
let subtitleFont = NSFont.systemFont(ofSize: 13, weight: .regular)
let subtitleAttrs: [NSAttributedString.Key: Any] = [
    .font: subtitleFont,
    .foregroundColor: NSColor(calibratedWhite: 0.65, alpha: 1.0)
]
let subtitleSize = (subtitle as NSString).size(withAttributes: subtitleAttrs)
let subtitlePoint = CGPoint(x: (width - subtitleSize.width) / 2, y: height - 85)
(subtitle as NSString).draw(at: subtitlePoint, withAttributes: subtitleAttrs)

// 7. Footer text
let footer = "macOS 14.0+ • Universal Binary (Apple Silicon & Intel)"
let footerAttrs: [NSAttributedString.Key: Any] = [
    .font: NSFont.systemFont(ofSize: 11, weight: .medium),
    .foregroundColor: NSColor(calibratedWhite: 0.40, alpha: 1.0)
]
let footerSize = (footer as NSString).size(withAttributes: footerAttrs)
let footerPoint = CGPoint(x: (width - footerSize.width) / 2, y: 30)
(footer as NSString).draw(at: footerPoint, withAttributes: footerAttrs)

NSGraphicsContext.restoreGraphicsState()

guard let pngData = rep.representation(using: .png, properties: [:]) else {
    fatalError("Failed to convert image to PNG")
}

let outputPath = CommandLine.arguments.count > 1 ? CommandLine.arguments[1] : "background.png"
try pngData.write(to: URL(fileURLWithPath: outputPath))
print("Successfully generated DMG background at \(outputPath)")
