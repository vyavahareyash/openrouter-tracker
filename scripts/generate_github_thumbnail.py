#!/usr/bin/env python3
"""
Generate GitHub Repository Social Preview Thumbnail (1280x640 px, 2:1 aspect ratio)
Concept A: Isometric Desk Hero with 3D floating macOS widgets and new circular app icon.
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 1280
HEIGHT = 640

def find_perspective_coeffs(pa, pb):
    """
    Find coefficients for PIL perspective transform.
    pa: points in target image (quad)
    pb: points in source image (rect)
    """
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    A = np.matrix(matrix, dtype=float)
    B = np.array(pb).reshape(8)
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

def transform_isometric(img, yaw=-18, pitch=14, roll=-4, scale=0.82):
    """
    Apply a 3D perspective projection to a 2D image.
    """
    w, h = img.size
    cx, cy = w / 2.0, h / 2.0
    
    rad_yaw = math.radians(yaw)
    rad_pitch = math.radians(pitch)
    rad_roll = math.radians(roll)
    
    # 3D corners centered at origin
    pts_3d = [
        [-cx, -cy, 0],
        [ cx, -cy, 0],
        [ cx,  cy, 0],
        [-cx,  cy, 0]
    ]
    
    # Rotation matrices
    # R_yaw (around Y), R_pitch (around X), R_roll (around Z)
    pts_proj = []
    focal = 1200.0
    
    for x, y, z in pts_3d:
        # Pitch (X)
        y1 = y * math.cos(rad_pitch) - z * math.sin(rad_pitch)
        z1 = y * math.sin(rad_pitch) + z * math.cos(rad_pitch)
        x1 = x
        
        # Yaw (Y)
        x2 = x1 * math.cos(rad_yaw) + z1 * math.sin(rad_yaw)
        z2 = -x1 * math.sin(rad_yaw) + z1 * math.cos(rad_yaw)
        y2 = y1
        
        # Roll (Z)
        x3 = x2 * math.cos(rad_roll) - y2 * math.sin(rad_roll)
        y3 = x2 * math.sin(rad_roll) + y2 * math.cos(rad_roll)
        z3 = z2
        
        # Perspective projection
        factor = focal / (focal + z3) * scale
        px = x3 * factor
        py = y3 * factor
        pts_proj.append((px, py))
        
    # Find bounding box of projected points
    xs = [p[0] for p in pts_proj]
    ys = [p[1] for p in pts_proj]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    out_w = int(max_x - min_x + 60)
    out_h = int(max_y - min_y + 60)
    
    # Offset points to fit in out_w, out_h
    offset_x = -min_x + 30
    offset_y = -min_y + 30
    dst_pts = [(p[0] + offset_x, p[1] + offset_y) for p in pts_proj]
    src_pts = [(0, 0), (w, 0), (w, h), (0, h)]
    
    coeffs = find_perspective_coeffs(dst_pts, src_pts)
    transformed = img.transform((out_w, out_h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    return transformed

def draw_radial_glow(canvas, center_x, center_y, radius, color):
    """
    Draw a smooth radial glow on canvas. color: (r, g, b, alpha)
    """
    glow = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    r, g, b, a = color
    for i in range(radius, 0, -4):
        alpha = int(a * (1.0 - (i / radius)) ** 1.8)
        draw.ellipse([radius - i, radius - i, radius + i, radius + i], fill=(r, g, b, alpha))
    canvas.alpha_composite(glow, (center_x - radius, center_y - radius))

def get_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

def create_thumbnail():
    # 1. Base Canvas
    img = Image.new("RGBA", (WIDTH, HEIGHT), (10, 14, 24, 255))
    
    # Draw background vertical / diagonal gradient
    bg = Image.new("RGBA", (WIDTH, HEIGHT))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(9 + 7 * t)
        g = int(13 + 9 * t)
        b = int(22 + 18 * t)
        bg_draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))
    img.paste(bg, (0, 0))
    
    # Subtle dot matrix grid pattern
    grid = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid)
    for x in range(20, WIDTH, 40):
        for y in range(20, HEIGHT, 40):
            g_draw.rectangle([x, y, x + 1, y + 1], fill=(255, 255, 255, 14))
    img.alpha_composite(grid)
    
    # 2. Ambient Glows
    draw_radial_glow(img, 280, 260, 320, (140, 60, 220, 48))    # Purple glow left
    draw_radial_glow(img, 920, 310, 380, (0, 190, 255, 65))     # Cyan glow right
    draw_radial_glow(img, 1100, 180, 260, (99, 102, 241, 40))   # Indigo glow top right
    
    # 3. 3D Floating Widgets (Right side)
    widget_med_src = Image.open("screenshots/widget_medium_dark.png").convert("RGBA")
    widget_sml_src = Image.open("screenshots/widget_small_dark.png").convert("RGBA")
    
    # 3a. Small widget (background depth)
    sml_3d = transform_isometric(widget_sml_src, yaw=-12, pitch=12, roll=-2, scale=0.62)
    sml_shadow = Image.new("RGBA", sml_3d.size, (0, 0, 0, 0))
    sml_alpha = sml_3d.split()[3]
    sml_shadow.paste((0, 0, 0, 160), mask=sml_alpha)
    sml_shadow = sml_shadow.filter(ImageFilter.GaussianBlur(16))
    
    pos_sml = (870, 75)
    img.alpha_composite(sml_shadow, (pos_sml[0] - 8, pos_sml[1] + 20))
    img.alpha_composite(sml_3d, pos_sml)
    
    # 3b. Medium widget (foreground hero depth)
    med_3d = transform_isometric(widget_med_src, yaw=-14, pitch=13, roll=-3, scale=0.68)
    med_shadow = Image.new("RGBA", med_3d.size, (0, 0, 0, 0))
    med_alpha = med_3d.split()[3]
    med_shadow.paste((0, 0, 0, 210), mask=med_alpha)
    med_shadow = med_shadow.filter(ImageFilter.GaussianBlur(24))
    
    pos_med = (570, 215)
    img.alpha_composite(med_shadow, (pos_med[0] - 12, pos_med[1] + 30))
    img.alpha_composite(med_3d, pos_med)
    
    # 4. Left Hero Content
    draw = ImageDraw.Draw(img)
    
    # 4a. Top Category Pill: "NATIVE MACOS DESKTOP WIDGET"
    pill_x, pill_y = 80, 72
    pill_w, pill_h = 285, 30
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=15, fill=(18, 26, 44, 220), outline=(56, 189, 248, 90), width=1)
    # Luminous pulse dot
    draw.ellipse([pill_x + 14, pill_y + 10, pill_x + 24, pill_y + 20], fill=(0, 225, 255, 255))
    font_pill = get_font(12, bold=True)
    draw.text((pill_x + 32, pill_y + 7), "NATIVE MACOS DESKTOP WIDGET", font=font_pill, fill=(147, 197, 253, 255))
    
    # 4b. App Icon
    icon_src = Image.open("OpenRouterTrackerApp/AppIcon.png").convert("RGBA")
    icon_size = 112
    icon_resized = icon_src.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    
    # Circular mask for app icon
    mask = Image.new("L", (icon_size, icon_size), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.ellipse([0, 0, icon_size, icon_size], fill=255)
    
    icon_circle = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    icon_circle.paste(icon_resized, (0, 0), mask=mask)
    
    # Icon shadow
    icon_shadow = Image.new("RGBA", (icon_size + 40, icon_size + 40), (0, 0, 0, 0))
    is_draw = ImageDraw.Draw(icon_shadow)
    is_draw.ellipse([20, 20, 20 + icon_size, 20 + icon_size], fill=(0, 0, 0, 180))
    icon_shadow = icon_shadow.filter(ImageFilter.GaussianBlur(16))
    
    icon_x, icon_y = 80, 126
    img.alpha_composite(icon_shadow, (icon_x - 20, icon_y - 12))
    img.alpha_composite(icon_circle, (icon_x, icon_y))
    
    # Subtle chrome bevel border around circular icon
    draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], outline=(255, 255, 255, 70), width=2)
    
    # Title beside icon
    title_x = icon_x + icon_size + 24
    font_title = get_font(44, bold=True)
    draw.text((title_x, icon_y + 12), "OpenRouter", font=font_title, fill=(255, 255, 255, 255))
    draw.text((title_x, icon_y + 60), "Tracker", font=font_title, fill=(56, 189, 248, 255))
    
    # 4c. Subtitle / description
    font_sub = get_font(18, bold=False)
    desc_y = 265
    draw.text((80, desc_y), "Real-time AI balance, key budget gauge & rate limits", font=font_sub, fill=(203, 213, 225, 255))
    draw.text((80, desc_y + 28), "glanceable directly on your macOS desktop.", font=font_sub, fill=(148, 163, 184, 255))
    
    # 4d. Badges Grid (2x2) with crisp vector graphics
    badges = [
        ("bolt", "1-Click Interactive Refresh", (56, 189, 248)),
        ("lock", "Hardware Keychain Vault", (168, 85, 247)),
        ("battery", "Zero Background Daemons", (52, 211, 153)),
        ("chart", "Multi-Key Budget Tracking", (251, 191, 36)),
    ]
    
    badge_start_y = 350
    b_w, b_h = 226, 44
    font_b = get_font(13, bold=True)
    
    for idx, (icon_type, label, color) in enumerate(badges):
        bx = 80 + (idx % 2) * (b_w + 14)
        by = badge_start_y + (idx // 2) * (b_h + 12)
        
        # Pill card with glass glow
        draw.rounded_rectangle([bx, by, bx + b_w, by + b_h], radius=10, fill=(22, 30, 48, 210), outline=(255, 255, 255, 30), width=1)
        # Accent left pill indicator
        draw.rounded_rectangle([bx + 8, by + 10, bx + 11, by + b_h - 10], radius=2, fill=color)
        
        # Vector icons
        ix, iy = bx + 22, by + 15
        if icon_type == "bolt":
            # Lightning bolt
            pts = [(ix + 6, iy), (ix + 1, iy + 8), (ix + 6, iy + 8), (ix + 4, iy + 14), (ix + 11, iy + 6), (ix + 6, iy + 6)]
            draw.polygon(pts, fill=color)
        elif icon_type == "lock":
            # Padlock
            draw.arc([ix + 3, iy, ix + 9, iy + 7], 180, 0, fill=color, width=2)
            draw.rounded_rectangle([ix + 2, iy + 5, ix + 10, iy + 13], radius=2, fill=color)
        elif icon_type == "battery":
            # Power pulse / zero daemon
            draw.rounded_rectangle([ix + 1, iy + 2, ix + 10, iy + 13], radius=2, outline=color, width=2)
            draw.rectangle([ix + 3, iy, ix + 8, iy + 2], fill=color)
            draw.rectangle([ix + 3, iy + 5, ix + 8, iy + 10], fill=color)
        elif icon_type == "chart":
            # Multi-key bar chart
            draw.rectangle([ix + 1, iy + 8, ix + 3, iy + 13], fill=color)
            draw.rectangle([ix + 5, iy + 4, ix + 7, iy + 13], fill=color)
            draw.rectangle([ix + 9, iy + 1, ix + 11, iy + 13], fill=color)
            
        draw.text((bx + 40, by + 14), label, font=font_b, fill=(241, 245, 249, 255))
        
    # 4e. Footer note
    font_foot = get_font(13, bold=False)
    foot_y = 485
    draw.text((80, foot_y), "Compatible with macOS Sonoma & Sequoia • Swift & WidgetKit", font=font_foot, fill=(100, 116, 139, 255))
    
    # Save output
    os.makedirs("assets", exist_ok=True)
    out_path = "assets/thumbnail.png"
    img.save(out_path, "PNG", optimize=True)
    print(f"Successfully generated GitHub thumbnail: {out_path} ({WIDTH}x{HEIGHT})")

if __name__ == "__main__":
    create_thumbnail()
