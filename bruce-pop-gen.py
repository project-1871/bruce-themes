#!/usr/bin/env python3
"""Generate pop-culture-styled Bruce firmware themes, each with its own art style.

  p-cat          cute stickers: white-outlined candy-pink icons, sparkles, bubbly boot title with a bow
  hero-quest     8-bit pixel art: gold/green/blue sprites on a dark forest, heart-meter boot
  pixel-plumber  8-bit pixel art: bright sprites on sky blue, brick ground + ? blocks boot
  code-rain      green katakana code rain behind glowing icons, rain resolves into the title
  steampunk      engraved brass/copper icons with rivets on dark leather, turning gears boot
  comic-hero     halftone comic panels with thick ink outlines, BRUCE! starburst boot with POW/ZAP
  alien-arcade   80s arcade shooter: pixel icons on a starfield, marching original aliens boot
  rainbow-pony   glossy pastel badges with sparkles, rainbow-sweep boot with a unicorn
  wild-encounter 4-shade green handheld pixel art in menu boxes, battle-screen boot with an original chip creature

Inspired by classic pop culture. All art is drawn here from generic icon glyphs and shapes:
no official artwork, sprites or logos.

Usage: ./bruce-pop-gen.py [theme ...] [--littlefs]
"""
import argparse, json, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
NERD = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf"
NERD_BOLD = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"
PIXEL = ROOT / "fonts" / "PressStart2P-Regular.ttf"
BUBBLY = ROOT / "fonts" / "Fredoka.ttf"
CJK = "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc"
MENUS = ["wifi", "ble", "rf", "rfid", "fm", "ir", "files", "gps", "nrf", "interpreter",
         "clock", "lora", "others", "connect", "config"]


def hexrgb(s): return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
def rgb565(c): return format(((c[0] >> 3) << 11) | ((c[1] >> 2) << 5) | (c[2] >> 3), "x")


def glyph_mask(cp, size, box, font_path=NERD, yfrac=0.5):
    f = ImageFont.truetype(str(font_path), size)
    m = Image.new("L", (box, box), 0)
    d = ImageDraw.Draw(m)
    bb = d.textbbox((0, 0), chr(cp), font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((box - w) // 2 - bb[0], int(box * yfrac) - h // 2 - bb[1]), chr(cp), font=f, fill=255)
    return m


def solid(size, color): return Image.new("RGB", size, color)


# ───────────────────────── p-cat: stickers ─────────────────────────
PCAT = dict(
    bg="FFDDE8", text="D7001E", dim="B5657F", led="FF4F8B",
    fills=["D7001E", "FF4F8B", "FF8FB1", "E23C6E"], shadow="F2A7BF", sparkle="FFD400",
    icons={"wifi": 0xF015F, "ble": 0xF1589, "rf": 0xF1545, "rfid": 0xF0E44, "fm": 0xF0387, "ir": 0xF1970,
           "files": 0xF049A, "gps": 0xF10F1, "nrf": 0xF09F1, "interpreter": 0xF095A, "clock": 0xF0D9E,
           "lora": 0xF18FB, "others": 0xF011B, "connect": 0xF02D1, "config": 0xF0460})


def sparkle(d, x, y, r, c):
    d.polygon([(x, y - r), (x + r // 4, y - r // 4), (x + r, y), (x + r // 4, y + r // 4),
               (x, y + r), (x - r // 4, y + r // 4), (x - r, y), (x - r // 4, y - r // 4)], fill=c)


def pcat_icon(key, S, t):
    rnd = random.Random("pcat-" + key)
    bg, shadow = hexrgb(t["bg"]), hexrgb(t["shadow"])
    m = glyph_mask(t["icons"][key], int(S * 0.56), S)
    outline = m.filter(ImageFilter.MaxFilter(13))
    img = solid((S, S), bg)
    img.paste(solid((S, S), shadow), (4, 5), outline)
    img.paste(solid((S, S), (255, 255, 255)), (0, 0), outline)
    img.paste(solid((S, S), hexrgb(rnd.choice(t["fills"]))), (0, 0), m)
    d = ImageDraw.Draw(img)
    for _ in range(3):
        sparkle(d, rnd.choice([rnd.randint(10, 26), rnd.randint(S - 26, S - 10)]), rnd.randint(12, S - 12),
                rnd.randint(5, 9), hexrgb(rnd.choice([t["sparkle"], "FFFFFF"])))
    return img


def scale_center(m, s):
    """Scale a mask about its center, keeping the canvas size."""
    W, H = m.size
    r = m.resize((max(1, int(W * s)), max(1, int(H * s))))
    out = Image.new("L", (W, H), 0)
    out.paste(r, ((W - r.width) // 2, (H - r.height) // 2))
    return out


def pcat_boot(W, H, t):
    bg = hexrgb(t["bg"])
    f = ImageFont.truetype(str(BUBBLY), int(H * 0.30))
    f.set_variation_by_axes([700, 100])  # weight, width: bold
    frames, rnd = [], random.Random(3)
    spots = [(rnd.randint(15, W - 15), rnd.randint(15, H - 15)) for _ in range(14)]
    for i in range(8):
        img = solid((W, H), bg)
        d = ImageDraw.Draw(img)
        for k, (x, y) in enumerate(spots):  # floating hearts + sparkles, twinkling
            if (k + i) % 3 == 0: continue
            if k % 2: sparkle(d, x, y, 6, hexrgb(t["sparkle"]))
            else: d.text((x, y), chr(0xF02D1), font=ImageFont.truetype(NERD, 16), fill=hexrgb(t["fills"][2]), anchor="mm")
        s = 0.6 + 0.4 * min(1, i / 5) + (0.06 if i == 5 else 0)  # pop-in with a bounce
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).text((W // 2, int(H * 0.47)), "Bruce", font=f, fill=255, anchor="mm")
        m = scale_center(m, s)
        out = m.filter(ImageFilter.MaxFilter(9))
        img.paste(solid((W, H), hexrgb(t["shadow"])), (4, 5), out)
        img.paste(solid((W, H), (255, 255, 255)), (0, 0), out)
        img.paste(solid((W, H), hexrgb(t["text"])), (0, 0), m)
        # a bow on the B
        if i >= 5:
            bow = glyph_mask(0xF0678, 46, 60)
            img.paste(solid((60, 60), (255, 255, 255)), (int(W * 0.13), int(H * 0.16)), bow.filter(ImageFilter.MaxFilter(7)))
            img.paste(solid((60, 60), hexrgb(t["text"])), (int(W * 0.13), int(H * 0.16)), bow)
        frames.append(img.quantize(48, dither=Image.Dither.NONE))
    return frames


# ───────────────────── hero-quest / pixel-plumber: pixel art ─────────────────────
HERO = dict(
    bg="0B1F10", text="F8D878", dim="7FA070", led="38B848", grid=26,
    outline="000000", fills=[("F8B800", "FCE0A8"), ("38B848", "B8F818"), ("D82800", "F87858"), ("0078F8", "3CBCFC")],
    icons={"wifi": 0xF06D3, "ble": 0xF1841, "rf": 0xF140B, "rfid": 0xF0306, "fm": 0xF0387, "ir": 0xF11FD,
           "files": 0xF0498, "gps": 0xF018B, "nrf": 0xF10CF, "interpreter": 0xF0093, "clock": 0xF03D2,
           "lora": 0xF15BF, "others": 0xF0691, "connect": 0xF02D1, "config": 0xF04E5})
PLUMBER = dict(
    bg="5C94FC", text="FFFFFF", dim="1F3F9F", led="E40058", grid=26,
    outline="000000", fills=[("E40058", "FC9838"), ("00A800", "B8F818"), ("F8B800", "FCE0A8"), ("C84C0C", "FC9838")],
    icons={"wifi": 0xF015F, "ble": 0xF04CE, "rf": 0xF140B, "rfid": 0xF0306, "fm": 0xF0387, "ir": 0xF0238,
           "files": "PIPE", "gps": 0xF023B, "nrf": 0xF02A0, "interpreter": 0xF078B, "clock": 0xF0538,
           "lora": 0xF011A, "others": 0xF07DF, "connect": 0xF0297, "config": 0xF08EA})


def pixelate(mask, g):
    """Mask -> low-res 0/1 grid (list of lists)."""
    small = mask.resize((g, g), Image.BOX).point(lambda v: 255 if v > 90 else 0)
    px = small.load()
    return [[px[x, y] > 0 for x in range(g)] for y in range(g)]


def sprite(cells, fill, hi, outline, g):
    """Render a pixel grid with 1px outline and top-left highlight, at grid resolution (RGBA)."""
    im = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    px = im.load()
    on = lambda x, y: 0 <= x < g and 0 <= y < g and cells[y][x]
    for y in range(g):
        for x in range(g):
            if on(x, y):
                px[x, y] = hi + (255,) if (not on(x, y - 1) or not on(x - 1, y)) else fill + (255,)
            elif any(on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = outline + (255,)
    return im


def pixel_icon(key, S, t, style):
    rnd = random.Random(style + key)
    g = t["grid"]
    if t["icons"][key] == "PIPE":  # hand-drawn warp pipe
        cells = [[(5 <= x < g - 5 and 5 <= y < 10) or (7 <= x < g - 7 and 10 <= y < g - 2) for x in range(g)]
                 for y in range(g)]
        fill, hi = hexrgb("00A800"), hexrgb("B8F818")
    else:
        cells = pixelate(glyph_mask(t["icons"][key], int(S * 0.62), S, yfrac=0.48), g)
        fill, hi = (hexrgb(c) for c in rnd.choice(t["fills"]))
    spr = sprite(cells, fill, hi, hexrgb(t["outline"]), g).resize((S, S), Image.NEAREST)
    bg = solid((S, S), hexrgb(t["bg"]))
    d = ImageDraw.Draw(bg)
    cell = S / g
    if style == "hero":  # faint grass tufts
        for _ in range(5):
            x, y = int(rnd.randrange(g) * cell), int(rnd.randrange(g - 3, g) * cell)
            d.rectangle([x, y, x + cell - 1, y + cell - 1], fill=(22, 52, 26))
    else:  # a small cloud puff in the sky
        cx, cy = int(rnd.choice([2, g - 6]) * cell), int(rnd.randint(1, 3) * cell)
        for dx, dy, w in ((0, 1, 4), (1, 0, 2)):
            d.rectangle([cx + dx * cell, cy + dy * cell, cx + (dx + w) * cell - 1, cy + (dy + 1) * cell - 1], fill=(252, 252, 252))
    bg.paste(spr, (0, 0), spr)
    return bg


def hero_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 40)
    small = ImageFont.truetype(str(PIXEL), 10)
    heart = pixelate(glyph_mask(0xF02D1, 180, 200), 9)
    heart_img = sprite(heart, (216, 40, 0), (248, 120, 88), (0, 0, 0), 9).resize((27, 27), Image.NEAREST)
    empty_img = sprite(heart, (40, 40, 40), (70, 70, 70), (0, 0, 0), 9).resize((27, 27), Image.NEAREST)
    sword = pixel_icon("config", 90, t, "hero")
    frames = []
    for i in range(9):
        img = solid((W, H), hexrgb(t["bg"]))
        d = ImageDraw.Draw(img)
        d.rectangle([8, 8, W - 9, H - 9], outline=hexrgb(t["text"]), width=3)
        d.rectangle([14, 14, W - 15, H - 15], outline=hexrgb(t["dim"]), width=1)
        for k in range(6):  # heart meter fills up
            img.paste(heart_img if k < i else empty_img, (W // 2 - 99 + k * 33, 36), heart_img)
        d.text((W // 2 + 3, 122 + 3), "BRUCE", font=f, fill=(0, 0, 0), anchor="mm")
        d.text((W // 2, 122), "BRUCE", font=f, fill=hexrgb(t["text"]), anchor="mm")
        if i >= 6: d.text((W // 2, 190), "IT'S DANGEROUS TO GO", font=small, fill=hexrgb(t["dim"]), anchor="mm")
        if i >= 7: d.text((W // 2, 206), "ALONE! TAKE THIS.", font=small, fill=hexrgb(t["dim"]), anchor="mm")
        frames.append(img.quantize(32, dither=Image.Dither.NONE))
    return frames


def plumber_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 40)
    small = ImageFont.truetype(str(PIXEL), 10)
    q = pixel_icon("interpreter", 36, t, "plumber")
    frames = []
    for i in range(9):
        img = solid((W, H), hexrgb(t["bg"]))
        d = ImageDraw.Draw(img)
        for x in range(0, W, 24):  # brick ground
            for row, y in enumerate(range(H - 36, H, 12)):
                ox = 0 if row % 2 else 12
                d.rectangle([x - ox, y, x - ox + 23, y + 11], fill=(200, 76, 12), outline=(0, 0, 0))
        for k, bx in enumerate((W // 2 - 60, W // 2 - 18, W // 2 + 24)):  # ? blocks, one bumps
            by = 150 - (8 if i % 3 == k else 0)
            d.rectangle([bx, by, bx + 35, by + 35], fill=(248, 184, 0), outline=(0, 0, 0), width=2)
            d.text((bx + 18, by + 19), "?", font=ImageFont.truetype(str(PIXEL), 18), fill=(200, 76, 12), anchor="mm")
        y = min(78, -30 + i * 18)  # title drops in
        d.text((W // 2 + 3, y + 3), "BRUCE", font=f, fill=(0, 0, 0), anchor="mm")
        d.text((W // 2, y), "BRUCE", font=f, fill=(255, 255, 255), anchor="mm")
        if i >= 7: d.text((W // 2, 118), "PRESS START", font=small, fill=(255, 255, 255), anchor="mm")
        frames.append(img.quantize(32, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── code-rain ─────────────────────────
RAIN = dict(
    bg="000000", text="00FF41", dim="008F11", led="00FF41",
    icons={"wifi": 0xF0602, "ble": 0xF0907, "rf": 0xF140B, "rfid": 0xF0306, "fm": 0xF011E, "ir": 0xF04E0,
           "files": 0xF081C, "gps": 0xF01A4, "nrf": 0xF0003, "interpreter": 0xF0628, "clock": 0xF0150,
           "lora": 0xF1119, "others": 0xF0402, "connect": 0xF0318, "config": 0xF04A5})
KATA = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789Z:.\"=*+-<>"


def rain(W, H, rnd, step, cols_on=0.55, fsize=13, phase=0):
    img = solid((W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(CJK, fsize, index=0)
    for cx in range(0, W, step):
        r = random.Random(rnd.random())
        if r.random() > cols_on: continue
        head = (r.randint(0, H // step + 8) + phase) % (H // step + 10)
        tail = r.randint(4, 12)
        for k in range(tail):
            row = head - k
            if row < 0 or row * step > H: continue
            v = 1 - k / tail
            c = (180, 255, 190) if k == 0 else (0, int(60 + 120 * v), int(15 + 30 * v))
            d.text((cx + step // 2, row * step + step // 2), r.choice(KATA), font=f, fill=c, anchor="mm")
    return img


def rain_icon(key, S, t):
    rnd = random.Random("rain-" + key)
    img = rain(S, S, rnd, 14, 0.5).point(lambda v: int(v * 0.55))
    m = glyph_mask(t["icons"][key], int(S * 0.6), S)
    halo = m.filter(ImageFilter.MaxFilter(11))
    img.paste((0, 0, 0), (0, 0), halo)
    g = m.filter(ImageFilter.GaussianBlur(5)).point(lambda v: min(255, v * 2))
    img.paste(solid((S, S), (0, 110, 30)), (0, 0), g)
    img.paste(solid((S, S), (0, 255, 65)), (0, 0), m)
    return img


def rain_boot(W, H, t):
    f = ImageFont.truetype(NERD_BOLD, 58)
    small = ImageFont.truetype(NERD, 13)
    frames = []
    for i in range(8):
        img = rain(W, H, random.Random(11), 16, 0.7, 15, phase=i * 3)
        if i >= 4:
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).text((W // 2, H // 2 - 8), "BRUCE", font=f, fill=255, anchor="mm")
            img = Image.composite(solid((W, H), (0, 0, 0)), img, m.filter(ImageFilter.MaxFilter(15)))
            img.paste(solid((W, H), (0, 120, 30)), (0, 0), m.filter(ImageFilter.GaussianBlur(6)))
            img.paste(solid((W, H), (0, 255, 65) if i > 4 else (200, 255, 210)), (0, 0), m)
        if i >= 6:
            ImageDraw.Draw(img).text((W // 2, H // 2 + 40), "wake up, neo...", font=small, fill=(0, 200, 60), anchor="mm")
        frames.append(img.quantize(24, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── steampunk: brass & gears ─────────────────────────
VICTORIAN = ROOT / "fonts" / "CinzelDecorative-Bold.ttf"
STEAM = dict(
    bg="1E140C", text="E8C170", dim="8A6A3E", led="D4892A",
    metals=[("FFE7A3", "B8862B", "5C3D12"), ("FFC9A0", "B8652B", "5A2A10"), ("F2F2E0", "A89F7A", "4F4A38")],
    icons={"wifi": 0xF001C, "ble": 0xF0210, "rf": 0xF029A, "rfid": 0xF030B, "fm": 0xF009A, "ir": 0xF0349,
           "files": 0xF0A6A, "gps": 0xF1382, "nrf": 0xF0347, "interpreter": 0xF14F7, "clock": 0xF1442,
           "lora": 0xF0B4E, "others": 0xF0BA4, "connect": 0xF052C, "config": 0xF08D6})


def gear_mask(size, r_out, teeth, angle, hole=0.28, spokes=5):
    """A cog as an L mask, centred, rotated by angle (radians)."""
    import math
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    c, r_in = size / 2, r_out * 0.80
    pts = []
    for i in range(teeth * 4):
        a = angle + i * math.pi * 2 / (teeth * 4)
        r = r_out if i % 4 in (1, 2) else r_in
        pts.append((c + r * math.cos(a), c + r * math.sin(a)))
    d.polygon(pts, fill=255)
    rim = r_in * 0.78
    d.ellipse([c - rim, c - rim, c + rim, c + rim], fill=0)
    for k in range(spokes):  # spokes
        a = angle + k * math.pi * 2 / spokes
        d.line([(c, c), (c + rim * math.cos(a), c + rim * math.sin(a))], fill=255, width=max(2, int(r_out * 0.16)))
    h = r_out * hole
    d.ellipse([c - h, c - h, c + h, c + h], fill=255)
    d.ellipse([c - h / 2, c - h / 2, c + h / 2, c + h / 2], fill=0)
    return m


def metal(size, light, mid, dark):
    """Vertical brushed-metal gradient."""
    W, H = size
    g = Image.new("RGB", (1, H))
    for y in range(H):
        v = y / max(1, H - 1)
        a, b, t = (light, mid, v / 0.45) if v < 0.45 else (mid, dark, (v - 0.45) / 0.55)
        g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * min(1, t)) for i in range(3)))
    return g.resize((W, H))


def steam_icon(key, S, t):
    import math
    rnd = random.Random("steam-" + key)
    bg = hexrgb(t["bg"])
    img = solid((S, S), bg)
    wm = gear_mask(S * 2, S * 0.9, 12, rnd.random())  # faint gear watermark in a corner
    wm = wm.crop((S // 2 + rnd.choice([-40, 40]), S // 2 + rnd.choice([-40, 40]), S // 2 + S + rnd.choice([-40, 40]),
                  S // 2 + S + rnd.choice([-40, 40]))).resize((S, S))
    img.paste(solid((S, S), tuple(min(255, c + 14) for c in bg)), (0, 0), wm)
    light, mid, dark = (hexrgb(c) for c in rnd.choice(t["metals"]))
    m = glyph_mask(t["icons"][key], int(S * 0.58), S)
    rim = m.filter(ImageFilter.MaxFilter(7))
    img.paste(solid((S, S), (0, 0, 0)), (3, 4), rim)                      # drop shadow
    img.paste(solid((S, S), tuple(c // 2 for c in dark)), (0, 0), rim)    # dark bezel
    img.paste(metal((S, S), light, mid, dark), (0, 0), m)                 # brass body
    d = ImageDraw.Draw(img)
    for x, y in ((9, 9), (S - 10, 9), (9, S - 10), (S - 10, S - 10)):     # corner rivets
        d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=mid, outline=dark)
        d.point((x - 1, y - 1), fill=light)
    return img


def steam_boot(W, H, t):
    import math
    bg = hexrgb(t["bg"])
    brass = [hexrgb(c) for c in t["metals"][0]]
    copper = [hexrgb(c) for c in t["metals"][1]]
    f = ImageFont.truetype(str(VICTORIAN), 44)
    small = ImageFont.truetype(str(VICTORIAN), 13)
    gears = [(70, 60, 58, 12, 1, brass), (150, 40, 34, 7, -12 / 7, copper), (262, 190, 64, 14, 12 / 14, copper),
             (205, 225, 30, 6, -14 / 6, brass)]
    frames = []
    for i in range(8):
        img = solid((W, H), bg)
        for cx, cy, r, teeth, ratio, (l, m_, dk) in gears:
            step = (math.pi * 2 / 12) * i / 8  # one tooth of the big gear over the loop
            gm = gear_mask(int(r * 2.2), r, teeth, step * ratio)
            x, y = int(cx - gm.width / 2), int(cy - gm.height / 2)
            img.paste(solid(gm.size, (0, 0, 0)), (x + 3, y + 4), gm)
            img.paste(metal(gm.size, l, m_, dk), (x, y), gm)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([34, 88, W - 34, 158], radius=10, fill=brass[1], outline=brass[2], width=3)  # plaque
        d.rounded_rectangle([40, 94, W - 40, 152], radius=7, outline=brass[0], width=1)
        for x in (46, W - 46):
            for y in (100, 146): d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=brass[2])
        d.text((W // 2 + 2, 124 + 2), "BRUCE", font=f, fill=brass[2], anchor="mm")
        d.text((W // 2, 124), "BRUCE", font=f, fill=(40, 24, 8), anchor="mm")
        if i >= 5: d.text((W // 2, 176), "~ patent pending ~", font=small, fill=hexrgb(t["text"]), anchor="mm")
        for k in range(3):  # steam puffs
            px, py = 150 + k * 9, 14 - ((i * 3 + k * 5) % 14)
            d.ellipse([px - 6, py - 4, px + 6, py + 4], fill=(90, 80, 70))
        frames.append(img.quantize(48, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── comic-hero: halftone comic book ─────────────────────────
COMIC_FONT = ROOT / "fonts" / "Bangers-Regular.ttf"
COMIC = dict(
    bg="FFF4D6", text="111111", dim="8A6A4A", led="E23636",
    panels=[("F7D117", "F29B12"), ("2E86DE", "7CB8F5"), ("E23636", "F58A8A"), ("35C46A", "9BE8B5")],
    fills=["FFFFFF", "F7D117", "E23636", "2E86DE"],
    icons={"wifi": 0xF0437, "ble": 0xF0AE2, "rf": 0xF0241, "rfid": 0xF113B, "fm": 0xF0D02, "ir": 0xF0B94,
           "files": 0xF14F7, "gps": 0xF04FE, "nrf": 0xF0768, "interpreter": 0xF06A9, "clock": 0xF1442,
           "lora": 0xF0471, "others": 0xF11EA, "connect": 0xF0FD7, "config": 0xF08EA})


def halftone(size, base, dot, step=11, r=3):
    img = solid(size, base)
    d = ImageDraw.Draw(img)
    for y in range(0, size[1] + step, step):
        for x in range((y // step % 2) * step // 2, size[0] + step, step):
            d.ellipse([x - r, y - r, x + r, y + r], fill=dot)
    return img


def burst(cx, cy, r_out, r_in, points, angle=0):
    import math
    return [(cx + (r_out if i % 2 == 0 else r_in) * math.cos(angle + i * math.pi / points),
             cy + (r_out if i % 2 == 0 else r_in) * math.sin(angle + i * math.pi / points)) for i in range(points * 2)]


def comic_icon(key, S, t):
    rnd = random.Random("comic-" + key)
    base, dot = (hexrgb(c) for c in rnd.choice(t["panels"]))
    img = halftone((S, S), base, dot, step=15, r=3)
    fill = hexrgb(rnd.choice([c for c in t["fills"] if hexrgb(c) != base]))
    m = glyph_mask(t["icons"][key], int(S * 0.56), S)
    ink = m.filter(ImageFilter.MaxFilter(9))
    img.paste(solid((S, S), (17, 17, 17)), (5, 6), ink)   # offset ink shadow
    img.paste(solid((S, S), (17, 17, 17)), (0, 0), ink)   # thick outline
    img.paste(solid((S, S), fill), (0, 0), m)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(17, 17, 17), width=4)  # panel border
    return img


def comic_boot(W, H, t):
    f = ImageFont.truetype(str(COMIC_FONT), 78)
    sfx = ImageFont.truetype(str(COMIC_FONT), 30)
    ink = (17, 17, 17)
    frames = []
    for i in range(8):
        img = halftone((W, H), hexrgb("E23636"), hexrgb("F58A8A"), 18, 4)
        d = ImageDraw.Draw(img)
        d.polygon(burst(W // 2 + 4, H // 2 + 5, 150, 95, 14), fill=ink)
        d.polygon(burst(W // 2, H // 2, 150, 95, 14), fill=hexrgb("F7D117"), outline=ink)
        if i >= 1:
            shake = [(0, 0), (5, -4), (-4, 3), (2, -1)][min(i - 1, 3)] if i < 5 else (0, 0)
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).text((W // 2 + shake[0], H // 2 + shake[1]), "BRUCE!", font=f, fill=255, anchor="mm")
            img.paste(solid((W, H), ink), (4, 5), m.filter(ImageFilter.MaxFilter(7)))
            img.paste(solid((W, H), ink), (0, 0), m.filter(ImageFilter.MaxFilter(7)))
            img.paste(solid((W, H), (255, 255, 255)), (0, 0), m)
        if i >= 5:
            for (x, y, word, col, ang) in ((52, 36, "POW!", "2E86DE", -0.3), (268, 206, "ZAP!", "35C46A", 0.25)):
                d = ImageDraw.Draw(img)
                d.polygon(burst(x, y, 40, 26, 9, ang), fill=(255, 255, 255), outline=ink)
                d.text((x, y), word, font=sfx, fill=hexrgb(col), anchor="mm", stroke_width=2, stroke_fill=ink)
        frames.append(img.quantize(12, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── alien-arcade: 80s arcade shooter ─────────────────────────
ARCADE = dict(
    bg="000000", text="FFFFFF", dim="20FF20", led="20FF20", grid=26,
    colors=["FFFFFF", "20FF20", "20E0FF", "FF40FF", "FFE020"],
    icons={"wifi": 0xF0437, "ble": 0xF10C4, "rf": 0xF140B, "rfid": 0xF030B, "fm": 0xF07F4, "ir": 0xF0208,
           "files": 0xF0A6A, "gps": 0xF05DD, "nrf": 0xF089A, "interpreter": 0xF0EB5, "clock": 0xF1442,
           "lora": 0xF0463, "others": 0xF1741, "connect": 0xF01E7, "config": 0xF0493})
# original alien designs (not the arcade classics): a tentacled jelly and a one-eyed walker, two frames each
JELLY = [["...XXXXX...", ".XXXXXXXXX.", "XX..XXX..XX", "XXXXXXXXXXX", ".X.X.X.X.X.", "X.X.X.X.X.X"],
         ["...XXXXX...", ".XXXXXXXXX.", "XX..XXX..XX", "XXXXXXXXXXX", "X.X.X.X.X.X", ".X.X.X.X.X."]]
CYCLOPS = [["....XXX....", "..XXXXXXX..", ".XXX...XXX.", ".XXX.X.XXX.", ".XXX...XXX.", "..XXXXXXX..", ".X..X.X..X.", "X...X.X...X"],
           ["....XXX....", "..XXXXXXX..", ".XXX...XXX.", ".XXX.X.XXX.", ".XXX...XXX.", "..XXXXXXX..", "..X.X.X.X..", ".X..X.X..X."]]
CANNON = [".....X.....", "....XXX....", ".XXXXXXXXX.", "XXXXXXXXXXX", "XXXXXXXXXXX"]


def draw_bits(d, rows, x, y, px, color):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "X": d.rectangle([x + i * px, y + j * px, x + (i + 1) * px - 1, y + (j + 1) * px - 1], fill=color)


def scanlines(img, every=3, factor=0.72):
    px = img.load()
    for y in range(0, img.height, every):
        for x in range(img.width):
            r, g, b = px[x, y][:3]
            px[x, y] = (int(r * factor), int(g * factor), int(b * factor))
    return img


def arcade_icon(key, S, t):
    rnd = random.Random("arcade-" + key)
    g = t["grid"]
    cells = pixelate(glyph_mask(t["icons"][key], int(S * 0.62), S, yfrac=0.5), g)
    col = hexrgb(rnd.choice(t["colors"]))
    hi = tuple(min(255, c + 90) for c in col)
    spr = sprite(cells, col, hi, (0, 0, 0), g).resize((S, S), Image.NEAREST)
    img = solid((S, S), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(9):  # starfield
        x, y = rnd.randrange(S), rnd.randrange(S)
        d.point((x, y), fill=(rnd.randint(90, 200),) * 3)
    img.paste(spr, (0, 0), spr)
    return img


def arcade_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 34)
    small = ImageFont.truetype(str(PIXEL), 10)
    rnd = random.Random(5)
    stars = [(rnd.randrange(W), rnd.randrange(H)) for _ in range(40)]
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for x, y in stars: d.point((x, (y + i * 2) % H), fill=(110, 110, 130))
        d.text((8, 8), "SCORE 1337", font=small, fill=(255, 255, 255))
        d.text((W - 8, 8), "HI 9999", font=small, fill=(255, 255, 255), anchor="ra")
        d.text((W // 2, 50), "BRUCE", font=f, fill=hexrgb("20FF20"), anchor="mm")
        march = (i % 4) * 4 - 6
        for row, (shape, col) in enumerate(((CYCLOPS, "FF40FF"), (JELLY, "20E0FF"), (JELLY, "20E0FF"))):
            for k in range(6):
                draw_bits(d, shape[i % 2], 40 + k * 42 + march, 82 + row * 26, 2, hexrgb(col))
        cx = 60 + i * 26
        draw_bits(d, CANNON, cx, 208, 2, hexrgb("20FF20"))
        if i % 2 == 0: d.rectangle([cx + 10, 150, cx + 11, 200], fill=(255, 255, 255))  # laser
        d.line([(0, 222), (W, 222)], fill=hexrgb("20FF20"), width=2)
        if i % 2: d.text((W // 2, 232), "INSERT COIN", font=small, fill=(255, 224, 32), anchor="mm")
        frames.append(scanlines(img).quantize(16, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── rainbow-pony: pastel badges & rainbows ─────────────────────────
SCRIPT_FONT = ROOT / "fonts" / "Pacifico-Regular.ttf"
PONY = dict(
    bg="F3E8FF", text="9B4DCA", dim="B98FD6", led="FF7EB9",
    badges=[("FFC7E3", "FF7EB9"), ("E2CCFF", "A77BFF"), ("C4EBFF", "5DBBFF"), ("C9F7DC", "4FD18B"),
            ("FFF4B8", "FFC83D"), ("FFDCC4", "FF935C")],
    rainbow=["FF6B9E", "FF9F5C", "FFD84D", "6EDC8C", "5DBBFF", "A77BFF"],
    icons={"wifi": 0xF015F, "ble": 0xF1589, "rf": 0xF1844, "rfid": 0xF0B8A, "fm": 0xF0F70, "ir": 0xF0E30,
           "files": 0xF1A1D, "gps": 0xF1741, "nrf": 0xF0A26, "interpreter": 0xF095A, "clock": 0xF0599,
           "lora": 0xF1985, "others": 0xF15C2, "connect": 0xF0A56, "config": 0xF01A5})


def pony_icon(key, S, t):
    rnd = random.Random("pony-" + key)
    light, deep = (hexrgb(c) for c in rnd.choice(t["badges"]))
    img = solid((S, S), hexrgb(t["bg"]))
    d = ImageDraw.Draw(img)
    r = int(S * 0.43)
    c = S // 2
    badge = Image.new("L", (S, S), 0)
    ImageDraw.Draw(badge).ellipse([c - r, c - r, c + r, c + r], fill=255)
    d.ellipse([c - r + 3, c - r + 5, c + r + 3, c + r + 5], fill=tuple(max(0, v - 40) for v in hexrgb(t["bg"])))  # soft shadow
    img.paste(metal((S, S), (255, 255, 255), light, deep), (0, 0), badge)                                      # glossy gradient
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 255, 255), width=4)
    d.ellipse([c - r * 0.62, c - r * 0.86, c + r * 0.2, c - r * 0.5], fill=tuple(min(255, v + 40) for v in light))  # shine
    m = glyph_mask(t["icons"][key], int(S * 0.46), S, yfrac=0.53)
    img.paste(solid((S, S), deep), (2, 3), m)
    img.paste(solid((S, S), (255, 255, 255)), (0, 0), m)
    for _ in range(3):
        sparkle(d, rnd.choice([rnd.randint(8, 22), rnd.randint(S - 22, S - 8)]), rnd.randint(10, S - 10),
                rnd.randint(4, 8), rnd.choice([deep, (255, 255, 255), hexrgb("FFC83D")]))
    return img


def pony_boot(W, H, t):
    f = ImageFont.truetype(str(SCRIPT_FONT), 66)
    small = ImageFont.truetype(str(BUBBLY), 15)
    small.set_variation_by_axes([700, 100])
    uni = glyph_mask(0xF15C2, 70, 90)
    cx, cy, R, band = W // 2, 200, 170, 14
    rnd = random.Random(8)
    spots = [(rnd.randint(10, W - 10), rnd.randint(10, H - 10)) for _ in range(12)]
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"]))
        d = ImageDraw.Draw(img)
        sweep = 180 * min(1, (i + 1) / 5)
        for k, col in enumerate(t["rainbow"]):  # rainbow arc sweeping left -> right
            rr = R - k * band
            d.pieslice([cx - rr, cy - rr, cx + rr, cy + rr], 180, 180 + sweep, fill=hexrgb(col))
        rr = R - len(t["rainbow"]) * band
        d.pieslice([cx - rr, cy - rr, cx + rr, cy + rr], 180, 360, fill=hexrgb(t["bg"]))
        for x in (cx - R + 40, cx + R - 40):  # clouds at the rainbow's ends
            for dx, dy, r in ((-22, 6, 16), (0, 0, 22), (22, 6, 16)):
                if x > cx and sweep < 180: continue
                d.ellipse([x + dx - r, cy - 8 + dy - r, x + dx + r, cy - 8 + dy + r], fill=(255, 255, 255))
        for k, (x, y) in enumerate(spots):
            if (k + i) % 3: sparkle(d, x, y, 6, hexrgb(rnd.choice(t["rainbow"])))
        if i >= 4:
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).text((W // 2, 96), "Bruce", font=f, fill=255, anchor="mm")
            out = m.filter(ImageFilter.MaxFilter(9))
            img.paste(solid((W, H), hexrgb(t["text"])), (3, 4), out)
            img.paste(solid((W, H), (255, 255, 255)), (0, 0), out)
            img.paste(solid((W, H), hexrgb(t["text"])), (0, 0), m)
            ux = 14 + (i - 4) * 6
            img.paste(solid((90, 90), (255, 255, 255)), (ux, 20), uni.filter(ImageFilter.MaxFilter(7)))
            img.paste(solid((90, 90), hexrgb("FF7EB9")), (ux, 20), uni)
        if i >= 6:
            ImageDraw.Draw(img).text((W // 2, 225), "sparkle on!", font=small, fill=hexrgb(t["text"]), anchor="mm")
        frames.append(img.quantize(48, dither=Image.Dither.NONE))
    return frames


# ───────────────────────── wild-encounter: 4-shade handheld monster game ─────────────────────────
DMG = ["9BBC0F", "8BAC0F", "306230", "0F380F"]  # lightest -> darkest, classic green handheld LCD
WILD = dict(
    bg=DMG[0], text=DMG[3], dim=DMG[2], led="40FF40", grid=26,
    icons={"wifi": 0xF05A9, "ble": 0xF15C6, "rf": 0xF140B, "rfid": 0xF0516, "fm": 0xF0387, "ir": 0xF0238,
           "files": 0xF0E10, "gps": 0xF034D, "nrf": 0xF058C, "interpreter": 0xF0AAF, "clock": 0xF0F65,
           "lora": 0xF0508, "others": 0xF03E9, "connect": 0xF04E1, "config": 0xF1130})
# the "wild BRUCE": an original microchip creature with pin legs (not from any game)
CHIP = ["....X..X..X..X..X.....",
        "....X..X..X..X..X.....",
        "..XXXXXXXXXXXXXXXXX...",
        "..X...............X...",
        "XXX..OO......OO...XXX.",
        "..X..OO......OO...X...",
        "XXX...............XXX.",
        "..X.....XXXXX.....X...",
        "XXX......XXX......XXX.",
        "..X...............X...",
        "XXX...X.......X...XXX.",
        "..XXXXXXXXXXXXXXXXX...",
        "....X..X..X..X..X.....",
        "...XX.XX..X..XX.XX...."]


def wild_icon(key, S, t):
    g = t["grid"]
    c = [hexrgb(x) for x in DMG]
    cells = pixelate(glyph_mask(t["icons"][key], int(S * 0.58), S, yfrac=0.5), g)
    spr = sprite(cells, c[2], c[2], c[3], g).resize((S, S), Image.NEAREST)  # solid fill reads best at 4 shades
    img = solid((S, S), c[0])
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([5, 5, S - 6, S - 6], radius=8, outline=c[3], width=4)   # menu-box frame
    d.rounded_rectangle([11, 11, S - 12, S - 12], radius=4, outline=c[1], width=2)
    img.paste(spr, (0, 0), spr)
    return img


def wild_boot(W, H, t):
    c = [hexrgb(x) for x in DMG]
    w, h = W // 2, H // 2  # draw at handheld-ish resolution, scale up 2x
    f = ImageFont.truetype(str(PIXEL), 8)

    def hp_box(d, x, y, name, lvl, frac, player=False):
        d.text((x, y), name, font=f, fill=c[3])
        d.text((x + 46, y), lvl, font=f, fill=c[3])
        d.text((x, y + 11), "HP", font=f, fill=c[3])
        d.rectangle([x + 18, y + 12, x + 66, y + 16], outline=c[3])
        d.rectangle([x + 19, y + 13, x + 19 + int(46 * frac), y + 15], fill=c[2])
        edge = x - 3 if player else x + 72  # the little bracket frame on the inner side
        d.line([(x - 3, y + 21), (x + 72, y + 21)], fill=c[3])
        d.line([(edge, y + 5), (edge, y + 21)], fill=c[3])

    frames, lines = [], ("A wild BRUCE", "appeared!")
    for i in range(10):
        img = solid((w, h), c[0])
        d = ImageDraw.Draw(img)
        if i == 0:  # encounter flash
            img = solid((w, h), c[3])
        elif i == 1:  # stripe wipe
            for y in range(0, h, 8): d.rectangle([0, y, w, y + 3], fill=c[3])
        else:
            slide = max(0, 90 - (i - 2) * 45)
            ox = 104 + slide
            d.ellipse([ox - 4, 42, ox + 44, 50], fill=c[1])  # ground shadow under the creature
            for yy, row in enumerate(CHIP):
                for xx, ch in enumerate(row):
                    if ch == "X": d.rectangle([ox + xx * 2, 12 + yy * 2, ox + xx * 2 + 1, 12 + yy * 2 + 1], fill=c[3])
                    elif ch == "O": d.rectangle([ox + xx * 2, 12 + yy * 2, ox + xx * 2 + 1, 12 + yy * 2 + 1], fill=c[2])
            if i >= 3:
                hp_box(d, 5, 5, "BRUCE", ":L99", 1.0)
                hp_box(d, 82, 58, "CYD", ":L42", 0.62, player=True)
            d.rectangle([0, 84, w - 1, h - 1], fill=c[0])
            d.rectangle([2, 86, w - 3, h - 3], outline=c[3], width=2)  # dialog box
            n = max(0, (i - 4) * 6)
            d.text((10, 95), lines[0][:n], font=f, fill=c[3])
            d.text((10, 107), lines[1][:max(0, n - len(lines[0]))], font=f, fill=c[3])
            if i >= 9: d.polygon([(w - 14, 108), (w - 8, 108), (w - 11, 112)], fill=c[3])  # "next" arrow
        frames.append(img.resize((W, H), Image.NEAREST).quantize(4, dither=Image.Dither.NONE))
    return frames


THEMES = {
    "p-cat": (PCAT, pcat_icon, pcat_boot),
    "hero-quest": (HERO, lambda k, S, t: pixel_icon(k, S, t, "hero"), hero_boot),
    "pixel-plumber": (PLUMBER, lambda k, S, t: pixel_icon(k, S, t, "plumber"), plumber_boot),
    "code-rain": (RAIN, rain_icon, rain_boot),
    "steampunk": (STEAM, steam_icon, steam_boot),
    "comic-hero": (COMIC, comic_icon, comic_boot),
    "alien-arcade": (ARCADE, arcade_icon, arcade_boot),
    "rainbow-pony": (PONY, pony_icon, pony_boot),
    "wild-encounter": (WILD, wild_icon, wild_boot),
}


def build_littlefs(theme_dir, name, out, size=0x30000, block=4096):
    from littlefs import LittleFS
    fs = LittleFS(block_size=block, block_count=size // block, name_max=64, disk_version=0x00020000)
    fs.mkdir(f"/{name}")
    for p in sorted(theme_dir.iterdir()):
        with fs.open(f"/{name}/{p.name}", "wb") as fh: fh.write(p.read_bytes())
    th = json.loads((theme_dir / f"{name}.json").read_text())
    conf = {k: th[k] for k in ("priColor", "secColor", "bgColor")}
    conf.update(themeFile=f"/{name}/{name}.json", themeOnSd=1)
    with fs.open("/bruce.conf", "w") as fh: fh.write(json.dumps(conf))
    out.write_bytes(fs.context.buffer)
    free = size // block - fs.used_block_count
    print(f"  LittleFS image: {out}  ({fs.used_block_count}/{size // block} blocks, {free} free)")
    if free < 3: print("  warning: too full, Bruce needs >4 KB free")


def build(name, a):
    t, icon_fn, boot_fn = THEMES[name]
    W, H, S = 320, 240, 132
    out = a.out / name
    out.mkdir(parents=True, exist_ok=True)
    pixel = name in ("hero-quest", "pixel-plumber", "alien-arcade", "wild-encounter")
    for key in MENUS:
        icon_fn(key, S, t).convert("RGB").save(out / f"{key}.jpg", quality=90 if pixel else 82,
                                               subsampling=0 if pixel else 2)
    frames = boot_fn(W, H, t)
    frames[0].save(out / "boot.gif", save_all=True, append_images=frames[1:],
                   duration=[140] * (len(frames) - 1) + [1500], loop=1, optimize=True)
    theme = {k: f"{k}.jpg" for k in MENUS}
    theme.update(priColor=rgb565(hexrgb(t["text"])), secColor=rgb565(hexrgb(t["dim"])), bgColor=rgb565(hexrgb(t["bg"])),
                 border=1, label=1, boot_img="boot.gif", ledBright=60, ledColor=t["led"], ledEffect=0,
                 ledEffectSpeed=3, ledEffectDirection=1)
    (out / f"{name}.json").write_text(json.dumps(theme, indent=2) + "\n")
    prev = a.out.parent / "previews" / a.out.name
    prev.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (5 * (S + 10) + 10, 3 * (S + 10) + 10), (0, 0, 0))
    for i, key in enumerate(MENUS):
        sheet.paste(Image.open(out / f"{key}.jpg"), (10 + (i % 5) * (S + 10), 10 + (i // 5) * (S + 10)))
    sheet.save(prev / f"{name}-icons.png")
    frames[-1].convert("RGB").save(prev / f"{name}-boot.png")
    frames[0].save(prev / f"{name}-boot.gif", save_all=True, append_images=frames[1:],
                   duration=[140] * (len(frames) - 1) + [1500], loop=0, optimize=True)
    kb = sum(p.stat().st_size for p in out.iterdir()) / 1024
    print(f"{name}: {out}/ ({kb:.0f} KB)")
    if a.littlefs: build_littlefs(out, name, ROOT / "local" / f"{name}-littlefs.bin")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help=", ".join(THEMES))
    ap.add_argument("--out", type=Path, default=ROOT / "pop")
    ap.add_argument("--littlefs", action="store_true")
    a = ap.parse_args()
    for n in a.names or THEMES:
        if n not in THEMES: sys.exit(f"unknown theme '{n}'")
        build(n, a)


if __name__ == "__main__":
    main()
