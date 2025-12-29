from PIL import Image
import os

ICON_PATH = r"C:/Users/xcn/.gemini/antigravity/brain/c20fda81-2476-423b-b4a7-56df0113bcaf/store_icon_128_1766051124764.png"
OUTPUT_PATH = r"C:\Users\xcn\.gemini\antigravity\brain\c20fda81-2476-423b-b4a7-56df0113bcaf\store_icon_128_final.png"

if os.path.exists(ICON_PATH):
    img = Image.open(ICON_PATH)
    print(f"Original Size: {img.size}")
    img = img.resize((128, 128), Image.Resampling.LANCZOS)
    img.save(OUTPUT_PATH)
    print(f"Saved Resized Icon: {OUTPUT_PATH}")
else:
    print("Icon not found")
