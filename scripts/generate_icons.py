#!/usr/bin/env python3
"""Generate extension icons from simple vector-style Pillow drawing commands."""

from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "icons"
ICONS.mkdir(parents=True, exist_ok=True)

size = 512
image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Rounded dark field with a blue edge.
draw.rounded_rectangle((18, 18, 494, 494), radius=112, fill="#0B0E14", outline="#557FFF", width=22)

# Bookmark body.
draw.rounded_rectangle((142, 92, 370, 350), radius=42, fill="#F5F7FA")
draw.polygon([(142, 300), (256, 410), (370, 300), (370, 360), (256, 466), (142, 360)], fill="#F5F7FA")

# Local export arrow.
draw.rounded_rectangle((234, 142, 278, 286), radius=20, fill="#557FFF")
draw.polygon([(180, 252), (332, 252), (256, 334)], fill="#557FFF")

for target in (16, 32, 48, 128):
    resized = image.resize((target, target), Image.Resampling.LANCZOS)
    resized.save(ICONS / f"icon{target}.png", optimize=True)

print("Generated icons:", ", ".join(f"icon{size}.png" for size in (16, 32, 48, 128)))
