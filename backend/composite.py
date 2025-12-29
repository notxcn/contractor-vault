import os
from PIL import Image, ImageFilter, ImageDraw, ImageFont

# Config
BG_PATH = r"C:/Users/xcn/.gemini/antigravity/brain/c20fda81-2476-423b-b4a7-56df0113bcaf/promo_background_tech_1766089978681.png"
SCREENSHOTS = [
    (r"C:/Users/xcn/.gemini/antigravity/brain/c20fda81-2476-423b-b4a7-56df0113bcaf/ui_share_1766090018766.png", "promo_1_share.png"),
    (r"C:/Users/xcn/.gemini/antigravity/brain/c20fda81-2476-423b-b4a7-56df0113bcaf/ui_claim_1766090030261.png", "promo_2_claim.png"),
    (r"C:/Users/xcn/.gemini/antigravity/brain/c20fda81-2476-423b-b4a7-56df0113bcaf/ui_home_1766090008707.png", "promo_3_home.png")
]
OUTPUT_DIR = r"C:\Users\xcn\.gemini\antigravity\brain\c20fda81-2476-423b-b4a7-56df0113bcaf"

def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def create_promo(screenshot_path, output_name):
    # Load Background
    if os.path.exists(BG_PATH):
        bg = Image.open(BG_PATH).convert("RGBA")
    else:
        # Fallback if BG missing: Solid Color
        bg = Image.new("RGBA", (1280, 800), (30, 41, 59))
        
    bg = bg.resize((1280, 800))

    # Load UI Screenshot
    ui = Image.open(screenshot_path).convert("RGBA")
    
    # Scale UI (Preserve aspect ratio, Max Height 600)
    # UI is 375x600.
    # No scaling needed, 600 fits in 800.
    
    # Add Rounded Corners?
    # UI is rectangle. Browser usually has corners?
    # Let's add slight rounding (10px).
    # ui = add_corners(ui, 10) # Complicated with alpha, skip for now.

    # Add Drop Shadow
    shadow = Image.new("RGBA", (ui.width + 40, ui.height + 40), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    # Shadow rect
    shadow_draw.rectangle((10, 10, ui.width + 30, ui.height + 30), fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    
    # Composite
    # Center position
    center_x = (bg.width - ui.width) // 2
    center_y = (bg.height - ui.height) // 2
    
    # Paste Shadow
    shadow_x = center_x - 20
    shadow_y = center_y - 20
    bg.paste(shadow, (shadow_x, shadow_y), shadow)
    
    # Paste UI
    bg.paste(ui, (center_x, center_y), ui)
    
    # Save
    out_path = os.path.join(OUTPUT_DIR, output_name)
    bg.convert("RGB").save(out_path)
    print(f"Created {out_path}")

print("Creating composites...")
for shot, name in SCREENSHOTS:
    if os.path.exists(shot):
        create_promo(shot, name)
    else:
        print(f"Missing screenshot: {shot}")
        
print("Done.")
