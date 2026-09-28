#!/usr/bin/env python3
"""Render each theme's main menu the way Bruce 1.16.1 draws it on the 320x240 CYD screen.

Writes previews/[<collection>/]<name>-menu.png: three menu pages (WiFi, RF, Clock) side by side.
Layout follows Bruce's MenuItemInterface::draw() + drawStatusBar(): themed image centered at y+13,
rounded border + status line, "BRUCE <version>" top-left, label in the 5x7 GLCD font at size 2.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
W, H, VERSION = 320, 240, "1.16.1"
PAGES = (("wifi", "WiFi"), ("rf", "RF"), ("clock", "Clock"))
COLLECTIONS = (("themes", "previews"), ("monster", "previews/monster"), ("pop", "previews/pop"))

# Adafruit GFX 5x7 font (BSD), ASCII 32..126, 5 column bytes per glyph, LSB = top row
GLCD = bytes.fromhex(
    "000000000000005f00000007000700147f147f14242a7f2a12231308646236495620500008070300001c2241000041221c00"
    "2a1c7f1c2a08083e080800807030000808080808000060600020100804023e5149453e00427f400072494949462141494d33"
    "1814127f1027454545393c4a49493141211109073649494936464949291e0000140000004034000000081422411414141414"
    "004122140802015909063e415d594e7c1211127c7f494949363e414141227f4141413e7f494949417f090909013e41415173"
    "7f0808087f00417f41002040413f017f081422417f404040407f021c027f7f0408107f3e4141413e7f090909063e4151215e"
    "7f09192946264949493203017f01033f4040403f1f2040201f3f4038403f631408146303047804036159494d43007f414141"
    "0204081020004141417f04020102044040404040000307080020545478407f284444383844444428384444287f3854545418"
    "00087e090218a4a49c787f0804047800447d40002040403d007f1028440000417f40007c047804787c080404783844444438"
    "fc1824241818242418fc7c08040408485454542404043f44243c4040207c1c2040201c3c4030403c44281028444c9090907c"
    "4464544c440008364100000077000000413608000201020402"
)


def rgb565(v):
    v = int(v, 16)
    return ((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31


def text(d, x, y, s, size, color):
    for ch in s:
        g = GLCD[(ord(ch) - 32) * 5:(ord(ch) - 31) * 5]
        for cx, col in enumerate(g):
            for cy in range(8):
                if col >> cy & 1:
                    d.rectangle((x + cx * size, y + cy * size, x + (cx + 1) * size - 1, y + (cy + 1) * size - 1), fill=color)
        x += 6 * size


def screen(tdir, t, key, label):
    pri, bg = rgb565(t["priColor"]), rgb565(t["bgColor"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)
    size = 2  # FM
    title_y = H // 2 + (H - 56) // 2 + 3  # iconCenterY + iconAreaH/2 + FG
    if t.get("label", 1):
        d.rectangle((10, title_y, W - 11, title_y + 16 - 1), fill=bg)
    icon = Image.open(tdir / t[key]).convert("RGB")
    r, g, b = icon.split()  # the panel is RGB565: quantize like the device so icon edges match the bg
    icon = Image.merge("RGB", (r.point(lambda v: (v >> 3) * 255 // 31), g.point(lambda v: (v >> 2) * 255 // 63),
                               b.point(lambda v: (v >> 3) * 255 // 31)))
    img.paste(icon, ((W - icon.width) // 2, 13 + (H - icon.height) // 2))
    if t.get("label", 1):
        d.rectangle((10, title_y, W - 11, title_y + 16 - 1), fill=bg)
        text(d, W // 2 - len(label) * 6 * size // 2, title_y, label, size, pri)
    if t.get("border", 1):
        d.rounded_rectangle((5, 5, W - 6, H - 6), 5, outline=pri)
        d.line((5, 25, W - 6, 25), fill=pri)
    d.rectangle((12, 12, 111, 19), fill=bg)
    text(d, 12, 12, "BRUCE " + VERSION, 1, pri)
    return img


def strip(tdir, t, gap=8):
    out = Image.new("RGB", (len(PAGES) * (W + gap) - gap, H), (8, 8, 10))
    for i, (key, label) in enumerate(PAGES):
        out.paste(screen(tdir, t, key, label), (i * (W + gap), 0))
    return out


if __name__ == "__main__":
    n = 0
    for coll, prev in COLLECTIONS:
        for tdir in sorted(p for p in (ROOT / coll).iterdir() if (p / f"{p.name}.json").exists()):
            t = json.loads((tdir / f"{tdir.name}.json").read_text())
            strip(tdir, t).save(ROOT / prev / f"{tdir.name}-menu.png", optimize=True)
            n += 1
    print(f"{n} menu previews")
