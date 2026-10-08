#!/usr/bin/env python3
"""
Generate GitHub README Motion Banner (Animated GIF + Static PNG Fallback)
Concept 2: Interactive Refresh Simulation
- Native macOS Widget with authentic glass aesthetic
- macOS cursor glides to the tactile refresh button
- 1-click button depression with expanding cyan ripple shockwave
- Refresh arrow spins 360 degrees with cubic ease
- Energy beam shimmer sweeps across widget and radial gauge
- Real-time balance and timestamp updates with emerald flash
- Rendered purely via code (PIL + numpy)
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH = 1080
HEIGHT = 440
TOTAL_FRAMES = 52
FPS = 18
FRAME_DURATION = int(1000 / FPS)  # ~55 ms

def get_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Menlo.ttc"
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_radial_glow(canvas, center_x, center_y, radius, color):
    glow = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    r, g, b, a = color
    for i in range(radius, 0, -4):
        alpha = int(a * (1.0 - (i / radius)) ** 1.8)
        draw.ellipse([radius - i, radius - i, radius + i, radius + i], fill=(r, g, b, alpha))
    canvas.alpha_composite(glow, (center_x - radius, center_y - radius))

def draw_cursor(canvas, x, y, clicking=False):
    """Draw crisp macOS pointer cursor at (x, y) with alpha blending"""
    cursor_img = Image.new("RGBA", (34, 34), (0, 0, 0, 0))
    draw = ImageDraw.Draw(cursor_img)
    scale = 0.9 if clicking else 1.0
    
    raw_pts = [(0, 0), (0, 20), (5, 15), (9, 23), (12, 21), (8, 14), (15, 14)]
    pts = [(int(px * scale), int(py * scale)) for px, py in raw_pts]
    
    # Shadow
    shadow_pts = [(px + 2, py + 2) for px, py in pts]
    draw.polygon(shadow_pts, fill=(0, 0, 0, 120))
    # Arrow body
    draw.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 240))
    
    canvas.alpha_composite(cursor_img, (int(x), int(y)))

def draw_refresh_symbol(canvas, cx, cy, angle_deg, radius=6.5, color=(165, 175, 190, 255)):
    """Draw circular arrow refresh symbol rotated by angle_deg onto canvas"""
    size = 40
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    center = size // 2
    
    # 270 degree arc
    draw.arc([center - radius, center - radius, center + radius, center + radius],
             start=-40, end=240, fill=color, width=2)
    
    # Arrowhead
    rad = math.radians(-40)
    tip_x = center + radius * math.cos(rad)
    tip_y = center + radius * math.sin(rad)
    head = [(tip_x - 1, tip_y - 4), (tip_x + 4, tip_y), (tip_x - 3, tip_y + 3)]
    draw.polygon(head, fill=color)
    
    rotated = icon.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, center=(center, center))
    canvas.alpha_composite(rotated, (int(cx - center), int(cy - center)))

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

def generate_motion_banner():
    print("Preparing motion banner...")
    os.makedirs("assets", exist_ok=True)
    
    # 1. Base widget setup
    widget_src = Image.open("screenshots/widget_medium_dark.png").convert("RGBA")
    w_orig, h_orig = widget_src.size
    
    scale = 0.84
    w_w = int(w_orig * scale)
    w_h = int(h_orig * scale)
    widget_scaled = widget_src.resize((w_w, w_h), Image.Resampling.LANCZOS)
    
    # Widget position on canvas
    wx = 425
    wy = 72
    
    # Exact center of the refresh button
    btn_orig_cx, btn_orig_cy = 605, 85
    btn_cx = wx + int(btn_orig_cx * scale)
    btn_cy = wy + int(btn_orig_cy * scale)
    
    # Pre-clean button patch in base widget (erase the static arrow so we draw a crisp rotating one)
    # The button area in widget_scaled has radius ~15
    patch_size = int(32 * scale)
    btn_patch_x = btn_cx - patch_size // 2
    btn_patch_y = btn_cy - patch_size // 2
    
    # Clean button background circle in widget
    clean_widget = widget_scaled.copy()
    cw_draw = ImageDraw.Draw(clean_widget)
    rel_btn_x = int(btn_orig_cx * scale)
    rel_btn_y = int(btn_orig_cy * scale)
    btn_r = int(14 * scale)
    # Fill with button background color
    cw_draw.ellipse([rel_btn_x - btn_r, rel_btn_y - btn_r, rel_btn_x + btn_r, rel_btn_y + btn_r],
                    fill=(36, 43, 56, 255), outline=(56, 68, 86, 200), width=1)
    
    # Timestamp area in clean_widget:
    time_rect_rel = (
        int(485 * scale),
        int(268 * scale),
        int(630 * scale),
        int(288 * scale)
    )
    
    # Balance area in clean_widget:
    bal_rect_rel = (
        int(408 * scale),
        int(162 * scale),
        int(540 * scale),
        int(212 * scale)
    )
    
    # 2. Build canvas background
    base_bg = Image.new("RGBA", (WIDTH, HEIGHT), (9, 12, 20, 255))
    bg_draw = ImageDraw.Draw(base_bg)
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 6 * t)
        g = int(11 + 8 * t)
        b = int(18 + 14 * t)
        bg_draw.line([(0, y), (WIDTH, y)], fill=(r, g, b, 255))
        
    # Dot matrix
    for x in range(20, WIDTH, 36):
        for y in range(20, HEIGHT, 36):
            bg_draw.rectangle([x, y, x + 1, y + 1], fill=(255, 255, 255, 12))
            
    # Ambient glows
    draw_radial_glow(base_bg, 200, 220, 280, (140, 60, 220, 42))   # Purple
    draw_radial_glow(base_bg, 760, 220, 320, (0, 190, 255, 55))    # Cyan
    
    # Left Hero Branding
    icon_src = Image.open("OpenRouterTrackerApp/AppIcon.png").convert("RGBA")
    icon_size = 84
    icon_resized = icon_src.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
    
    mask = Image.new("L", (icon_size, icon_size), 0)
    m_draw = ImageDraw.Draw(mask)
    m_draw.ellipse([0, 0, icon_size, icon_size], fill=255)
    
    icon_circle = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
    icon_circle.paste(icon_resized, (0, 0), mask=mask)
    
    icon_x, icon_y = 60, 72
    icon_shadow = Image.new("RGBA", (icon_size + 30, icon_size + 30), (0, 0, 0, 0))
    is_draw = ImageDraw.Draw(icon_shadow)
    is_draw.ellipse([15, 15, 15 + icon_size, 15 + icon_size], fill=(0, 0, 0, 180))
    icon_shadow = icon_shadow.filter(ImageFilter.GaussianBlur(14))
    base_bg.alpha_composite(icon_shadow, (icon_x - 15, icon_y - 10))
    base_bg.alpha_composite(icon_circle, (icon_x, icon_y))
    bg_draw.ellipse([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], outline=(255, 255, 255, 70), width=2)
    
    # Title
    f_title = get_font(34, bold=True)
    f_sub = get_font(14, bold=False)
    f_badge = get_font(12, bold=True)
    
    bg_draw.text((icon_x + icon_size + 18, icon_y + 6), "OpenRouter", font=f_title, fill=(255, 255, 255, 255))
    bg_draw.text((icon_x + icon_size + 18, icon_y + 44), "Tracker", font=f_title, fill=(56, 189, 248, 255))
    
    # Category tag
    bg_draw.text((60, 180), "Native macOS Desktop Widget", font=get_font(16, bold=True), fill=(226, 232, 240, 255))
    bg_draw.text((60, 206), "Real-time AI balance & token meter.", font=f_sub, fill=(148, 163, 184, 255))
    bg_draw.text((60, 226), "Interactive 1-click refresh without daemons.", font=f_sub, fill=(100, 116, 139, 255))
    
    # Feature Pills with vector shapes
    badges = [
        ("bolt", "1-Click Interactive Refresh", (56, 189, 248)),
        ("battery", "Zero Background Daemons", (52, 211, 153)),
        ("lock", "Hardware Keychain Vault", (168, 85, 247)),
    ]
    pill_y = 274
    for icon_t, text, col in badges:
        bg_draw.rounded_rectangle([60, pill_y, 350, pill_y + 34], radius=8, fill=(18, 25, 42, 200), outline=(255, 255, 255, 26), width=1)
        bg_draw.rounded_rectangle([60 + 6, pill_y + 8, 60 + 9, pill_y + 26], radius=2, fill=col)
        
        # Vector icon
        ix, iy = 60 + 20, pill_y + 11
        if icon_t == "bolt":
            pts = [(ix + 5, iy), (ix + 1, iy + 7), (ix + 5, iy + 7), (ix + 3, iy + 12), (ix + 9, iy + 5), (ix + 5, iy + 5)]
            bg_draw.polygon(pts, fill=col)
        elif icon_t == "battery":
            bg_draw.rounded_rectangle([ix + 1, iy + 1, ix + 8, iy + 11], radius=2, outline=col, width=1)
            bg_draw.rectangle([ix + 3, iy, ix + 6, iy + 1], fill=col)
            bg_draw.rectangle([ix + 3, iy + 4, ix + 6, iy + 9], fill=col)
        elif icon_t == "lock":
            bg_draw.arc([ix + 2, iy, ix + 7, iy + 6], 180, 0, fill=col, width=1)
            bg_draw.rounded_rectangle([ix + 1, iy + 5, ix + 8, iy + 12], radius=1, fill=col)
            
        bg_draw.text((60 + 36, pill_y + 10), text, font=f_badge, fill=(241, 245, 249, 255))
        pill_y += 44
        
    # Floating Widget Shadow
    w_shadow = Image.new("RGBA", (w_w + 60, w_h + 60), (0, 0, 0, 0))
    ws_draw = ImageDraw.Draw(w_shadow)
    ws_draw.rounded_rectangle([30, 30, 30 + w_w, 30 + w_h], radius=28, fill=(0, 0, 0, 220))
    w_shadow = w_shadow.filter(ImageFilter.GaussianBlur(24))
    base_bg.alpha_composite(w_shadow, (wx - 30, wy - 10))
    
    # Frames generation
    frames = []
    print(f"Rendering {TOTAL_FRAMES} frames...")
    
    c_start = (wx + w_w + 20, wy + w_h - 10)
    c_target = (btn_cx + 4, btn_cy + 4)
    
    for f in range(TOTAL_FRAMES):
        frame = base_bg.copy()
        
        # Clone clean widget
        current_widget = clean_widget.copy()
        cw_draw = ImageDraw.Draw(current_widget)
        
        # Timeline parameters
        # 0..14: cursor glide towards button
        # 15..20: click button (depression + shockwave ripple)
        # 21..37: 360 spin + energy wave + Updating...
        # 38..46: Updated Just Now (green) + balance flash $165.80
        # 47..51: settle & cursor retreat
        
        spin_angle = 0.0
        btn_scale = 1.0
        ripple_r = 0
        ripple_a = 0
        shimmer_t = -1.0
        
        if f < 15:
            # Gliding
            t = f / 14.0
            cur_x = c_start[0] + (c_target[0] - c_start[0]) * ease_out_quad(t)
            cur_y = c_start[1] + (c_target[1] - c_start[1]) * ease_out_quad(t)
            is_clicking = False
            show_cursor = (f >= 3)
            status_mode = "idle"
        elif f <= 20:
            # Click
            cur_x, cur_y = c_target
            is_clicking = True
            show_cursor = True
            cf = f - 15
            btn_scale = 0.92 if cf in [1, 2, 3] else 0.96
            if f >= 17:
                rf = f - 17
                ripple_r = int(8 + rf * 9)
                ripple_a = int(220 * (1.0 - rf / 4.0))
            status_mode = "idle"
        elif f <= 37:
            # Refreshing
            rf = f - 21
            spin_t = rf / 16.0
            spin_angle = 360.0 * ease_in_out_cubic(spin_t)
            shimmer_t = spin_t
            
            # Cursor drifts away
            cur_t = min(1.0, rf / 8.0)
            cur_x = c_target[0] + 35 * cur_t
            cur_y = c_target[1] + 25 * cur_t
            is_clicking = False
            show_cursor = (f < 32)
            status_mode = "updating"
        else:
            # Updated
            is_clicking = False
            show_cursor = False
            cur_x, cur_y = c_start
            status_mode = "done"
            
        # Draw dynamic timestamp onto current_widget
        f_time = get_font(int(8.5 * scale), bold=(status_mode == "done"))
        cw_draw.rectangle(time_rect_rel, fill=(23, 31, 44, 255))
        
        if status_mode == "idle":
            cw_draw.text((time_rect_rel[0] + 16, time_rect_rel[1] + 1), "Updated 5:48 PM",
                         font=f_time, fill=(148, 163, 184, 255))
        elif status_mode == "updating":
            pulse_a = int(180 + 75 * math.sin(f * 0.9))
            cw_draw.ellipse([time_rect_rel[0] + 6, time_rect_rel[1] + 7,
                             time_rect_rel[0] + 11, time_rect_rel[1] + 12], fill=(56, 189, 248, pulse_a))
            cw_draw.text((time_rect_rel[0] + 16, time_rect_rel[1] + 4), "Refreshing...",
                         font=f_time, fill=(56, 189, 248, pulse_a))
        elif status_mode == "done":
            cw_draw.ellipse([time_rect_rel[0] + 6, time_rect_rel[1] + 7,
                             time_rect_rel[0] + 11, time_rect_rel[1] + 12], fill=(16, 185, 129, 255))
            cw_draw.text((time_rect_rel[0] + 16, time_rect_rel[1] + 4), "Updated Just Now",
                         font=f_time, fill=(16, 185, 129, 255))
            
        # Composite widget to frame
        frame.alpha_composite(current_widget, (wx, wy))
        
        # Draw button highlight when clicked
        if is_clicking:
            overlay_btn = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            ob_draw = ImageDraw.Draw(overlay_btn)
            cur_r = int(btn_r * btn_scale)
            ob_draw.ellipse([btn_cx - cur_r, btn_cy - cur_r, btn_cx + cur_r, btn_cy + cur_r],
                            fill=(56, 189, 248, 45), outline=(56, 189, 248, 160), width=1)
            frame.alpha_composite(overlay_btn)
            
        # Draw rotating refresh icon
        arrow_col = (56, 189, 248, 255) if status_mode == "updating" else (160, 172, 188, 255)
        draw_refresh_symbol(frame, btn_cx, btn_cy, spin_angle, radius=int(6.2 * scale * btn_scale), color=arrow_col)
        
        # Draw Ripple shockwave
        if ripple_a > 0 and ripple_r > 0:
            rip = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
            r_draw = ImageDraw.Draw(rip)
            r_draw.ellipse([btn_cx - ripple_r, btn_cy - ripple_r, btn_cx + ripple_r, btn_cy + ripple_r],
                           outline=(0, 210, 255, ripple_a), width=2)
            frame.alpha_composite(rip)
            
        # Draw Energy Shimmer Beam
        if shimmer_t >= 0.0:
            beam_x = wx + int(w_w * (1.0 - shimmer_t * 1.15))
            if wx - 20 <= beam_x <= wx + w_w + 20:
                beam = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
                b_draw = ImageDraw.Draw(beam)
                b_alpha = int(40 * math.sin(shimmer_t * math.pi))
                b_draw.rectangle([beam_x - 30, wy + 10, beam_x + 30, wy + w_h - 10], fill=(0, 210, 255, b_alpha))
                beam = beam.filter(ImageFilter.GaussianBlur(12))
                frame.alpha_composite(beam)
                
        # Draw balance glow on update
        if status_mode == "done":
            glow_progress = max(0.0, 1.0 - (f - 38) / 9.0)
            if glow_progress > 0:
                draw_radial_glow(frame, wx + bal_rect_rel[0] + 50, wy + bal_rect_rel[1] + 20,
                                 35, (56, 189, 248, int(65 * glow_progress)))
                
        # Draw Cursor
        if show_cursor:
            draw_cursor(frame, cur_x, cur_y, clicking=is_clicking)
            
        frames.append(frame.convert("RGB"))
        
    # Save static PNG fallback (frame 0)
    static_png = "assets/banner.png"
    frames[0].save(static_png, "PNG", optimize=True)
    print(f"Saved static fallback banner: {static_png}")
    
    # Save animated GIF
    gif_path = "assets/banner.gif"
    print(f"Encoding animated GIF to {gif_path} (frames={TOTAL_FRAMES}, duration={FRAME_DURATION}ms)...")
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION,
        loop=0,
        optimize=True
    )
    size_mb = os.path.getsize(gif_path) / (1024 * 1024)
    print(f"Successfully generated motion banner: {gif_path} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    generate_motion_banner()
