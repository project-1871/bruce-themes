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


# ═════════════════════════ retro games & movies (batch 2) ═════════════════════════
from PIL import ImageChops
import math

BASE = {"wifi": 0xF05A9, "ble": 0xF00AF, "rf": 0xF043B, "rfid": 0xF0396, "fm": 0xF0439, "ir": 0xF0454,
        "files": 0xF024B, "gps": 0xF01A4, "nrf": 0xF0003, "interpreter": 0xF0169, "clock": 0xF0150,
        "lora": 0xF1119, "others": 0xF15FC, "connect": 0xF0318, "config": 0xF0493}


def icons(**over):
    d = dict(BASE); d.update(over); return d


def F(name): return ROOT / "fonts" / name


def vfont(path, size, wght=None):
    f = ImageFont.truetype(str(path), size)
    if wght:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f


MRROBOT = Path.home() / ".local/share/fonts/MrRobot.ttf"


def title_font(size):
    return ImageFont.truetype(str(MRROBOT if MRROBOT.exists() else F("Orbitron.ttf")), size)


def mask_of(t, key, S, scale=0.58, yfrac=0.5):
    return glyph_mask(t["icons"][key], int(S * scale), S, yfrac=yfrac)


def paint(img, mask, color, off=(0, 0)):
    img.paste(solid(img.size, color), off, mask)


def glowm(mask, r, k=2.0):
    return mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * k)))


def ring(mask, w=7):
    return ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(w)), mask)


def text_mask(size, xy, text, font, anchor="mm"):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).text(xy, text, font=font, fill=255, anchor=anchor)
    return m


def cycle(t, key, name="colors"):
    return hexrgb(t[name][MENUS.index(key) % len(t[name])])


def q(img, n): return img.quantize(n, dither=Image.Dither.NONE)


# ── 1 maze-chomper ──
MAZE = dict(bg="000000", text="FFE000", dim="2121DE", led="FFE000", grid=24,
            colors=["FFE000", "FF0000", "FFB8FF", "00FFFF", "FFB852"], icons=icons(others=0xF02A0))


def maze_icon(key, S, t):
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    blue = hexrgb("2121DE")
    d.rounded_rectangle([4, 4, S - 5, S - 5], radius=14, outline=blue, width=3)
    d.rounded_rectangle([11, 11, S - 12, S - 12], radius=9, outline=blue, width=3)
    for x in range(24, S - 20, 14): d.rectangle([x, S - 22, x + 3, S - 19], fill=hexrgb("FFB8AE"))
    g = t["grid"]; col = cycle(t, key)
    spr = sprite(pixelate(mask_of(t, key, S, 0.52, 0.45), g), col, col, (0, 0, 0), g).resize((S, S), Image.NEAREST)
    img.paste(spr, (0, 0), spr)
    return img


def maze_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 36); small = ImageFont.truetype(str(PIXEL), 10)
    blue, yellow = hexrgb("2121DE"), hexrgb("FFE000")
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        for inset in (6, 14): d.rounded_rectangle([inset, inset, W - 1 - inset, H - 1 - inset], radius=18, outline=blue, width=3)
        d.text((W // 2, 70), "BRUCE", font=f, fill=yellow, anchor="mm")
        px = 30 + i * 34
        for x in range(40, W - 30, 20):
            if x > px + 10: d.rectangle([x, 148, x + 4, 152], fill=hexrgb("FFB8AE"))
        mouth = 35 if i % 2 == 0 else 5
        d.pieslice([px - 16, 134, px + 16, 166], mouth, 360 - mouth, fill=yellow)
        for k, col in enumerate(("FF0000", "FFB8FF")):  # chasing ghosts
            gx = px - 60 - k * 40
            if gx > 10:
                gm = glyph_mask(0xF02A0, 34, 40)
                img.paste(solid((40, 40), hexrgb(col)), (gx - 20, 130), gm)
        if i >= 5: d.text((W // 2, 200), "READY!", font=small, fill=yellow, anchor="mm")
        frames.append(q(img, 8))
    return frames


# ── 2 block-stack ──
STACK = dict(bg="0A0A1A", text="FFFFFF", dim="00F0F0", led="A000F0", grid=13,
             colors=["00F0F0", "F0F000", "A000F0", "00F000", "F00000", "3060FF", "F0A000"], icons=icons())


def bevel_cell(d, x, y, c, col):
    light = tuple(min(255, v + 90) for v in col); dark = tuple(v // 2 for v in col)
    d.rectangle([x, y, x + c - 1, y + c - 1], fill=col)
    d.polygon([(x, y), (x + c - 1, y), (x + c - 4, y + 3), (x + 3, y + 3), (x + 3, y + c - 4), (x, y + c - 1)], fill=light)
    d.polygon([(x + c - 1, y), (x + c - 1, y + c - 1), (x, y + c - 1), (x + 3, y + c - 4), (x + c - 4, y + c - 4), (x + c - 4, y + 3)], fill=dark)


def stack_icon(key, S, t):
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    g = t["grid"]; c = S // g; off = (S - c * g) // 2
    for k in range(g + 1):
        d.line([(off + k * c, off), (off + k * c, off + g * c)], fill=(24, 24, 40))
        d.line([(off, off + k * c), (off + g * c, off + k * c)], fill=(24, 24, 40))
    cells = pixelate(mask_of(t, key, S, 0.66), g); col = cycle(t, key)
    for y in range(g):
        for x in range(g):
            if cells[y][x]: bevel_cell(d, off + x * c, off + y * c, c, col)
    return img


def stack_boot(W, H, t):
    c = 6; cols, rows = W // c, H // c
    m = text_mask((cols, rows), (cols // 2, rows // 2 - 4), "BRUCE", ImageFont.truetype(str(PIXEL), 8))
    px = m.load()
    on = [(x, y) for y in range(rows) for x in range(cols) if px[x, y] > 100]
    x0 = min(x for x, _ in on)
    colors = [hexrgb(x) for x in t["colors"]]
    frames = []
    for i in range(9):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        for x in range(0, W, c * 2): d.line([(x, 0), (x, H)], fill=(18, 18, 32))
        for y in range(0, H, c * 2): d.line([(0, y), (W, y)], fill=(18, 18, 32))
        for x, y in on:
            li = (x - x0) // 8  # which letter
            drop = max(0, li + 2 - i) * 7  # letters fall in one after another and land
            if i >= li: bevel_cell(d, x * c, (y - drop) * c, c, colors[li % len(colors)])
        base = rows - 4  # a full line at the bottom flashes and clears
        if i < 8:
            for x in range(cols): bevel_cell(d, x * c, base * c, c, (255, 255, 255) if i >= 7 else colors[(x // 5) % len(colors)])
        frames.append(q(img, 32))
    return frames


# ── 3 block-craft ──
CRAFT = dict(bg="2B2B2B", text="FFFFFF", dim="A0A0A0", led="5FAF3F", grid=22,
             colors=["4AEDD9", "FCEE4B", "D8D8D8", "FF3030", "17DD62"],
             tiles=[["866043", "7A5638", "96704F", "6C4C30"], ["7F7F7F", "747474", "8F8F8F", "6A6A6A"],
                    ["A0824E", "8E7244", "B08F57", "7D6440"]],
             icons=icons(files=0xF0726, config=0xF08B7, others=0xF04E5))


def craft_icon(key, S, t):
    rnd = random.Random("craft-" + key)
    shades = [hexrgb(x) for x in t["tiles"][MENUS.index(key) % 3]]
    img = solid((S, S), shades[0]); d = ImageDraw.Draw(img)
    c = S / 16
    for y in range(16):
        for x in range(16):
            d.rectangle([int(x * c), int(y * c), int((x + 1) * c) - 1, int((y + 1) * c) - 1], fill=rnd.choice(shades))
    if MENUS.index(key) % 3 == 0:  # grass top on dirt blocks
        for x in range(16):
            h = rnd.randint(2, 4)
            d.rectangle([int(x * c), 0, int((x + 1) * c) - 1, int(h * c) - 1], fill=rnd.choice([(95, 159, 53), (84, 140, 47), (110, 176, 64)]))
    g = t["grid"]; col = cycle(t, key)
    cells = pixelate(mask_of(t, key, S, 0.6, 0.52), g)
    spr = sprite(cells, col, tuple(min(255, v + 60) for v in col), (20, 20, 20), g).resize((S, S), Image.NEAREST)
    shadow = Image.new("L", (S, S), 0); shadow.paste(spr.split()[3], (6, 6))
    img.paste(solid((S, S), (30, 24, 18)), (0, 0), shadow)
    img.paste(spr, (0, 0), spr)
    return img


def craft_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 40); sp = ImageFont.truetype(str(PIXEL), 10)
    rnd = random.Random(4)
    ground = [[rnd.choice(["866043", "7A5638", "96704F"]) for _ in range(W // 10)] for _ in range(6)]
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb("7EB3FF")); d = ImageDraw.Draw(img)
        for gy, row in enumerate(ground):
            for gx, col in enumerate(row):
                fill = (95, 159, 53) if gy == 0 else hexrgb(col)
                d.rectangle([gx * 10, 180 + gy * 10, gx * 10 + 9, 180 + gy * 10 + 9], fill=fill)
        for gx in range(0, W // 10, 6):  # blocks stacking up
            h = min(i, 3 + (gx // 6) % 3)
            for k in range(h): d.rectangle([gx * 10, 170 - k * 10, gx * 10 + 9, 179 - k * 10], fill=hexrgb("7F7F7F"), outline=hexrgb("5A5A5A"))
        for dz in range(6, 0, -1): d.text((W // 2 + dz, 78 + dz), "BRUCE", font=f, fill=(60, 60, 60), anchor="mm")
        d.text((W // 2, 78), "BRUCE", font=f, fill=(200, 200, 200), anchor="mm")
        if i >= 4:
            s = 1.0 + (0.12 if i % 2 else 0)
            spl = Image.new("L", (160, 30), 0)
            ImageDraw.Draw(spl).text((80, 15), "Now with WiFi!", font=ImageFont.truetype(str(PIXEL), int(9 * s)), fill=255, anchor="mm")
            spl = spl.rotate(18, expand=True)
            img.paste(solid(spl.size, (255, 255, 0)), (W - spl.width - 6, 96), spl)
        frames.append(q(img, 24))
    return frames


# ── 4 wasteland-terminal / 14 magic-word helpers: CRT phosphor ──
WASTE = dict(bg="031A08", text="1AFF80", dim="0E8A45", led="1AFF80", phos="1AFF80",
             icons=icons(others=0xF043C, gps=0xF034D, interpreter=0xF018D))


def phosphor_icon(key, S, t):
    bg, ph = hexrgb(t["bg"]), hexrgb(t["phos"])
    img = solid((S, S), bg)
    m = mask_of(t, key, S, 0.56)
    paint(img, glowm(m, 6, 1.4), tuple(v // 3 for v in ph))
    paint(img, m, ph)
    d = ImageDraw.Draw(img); L = 16
    for (x, y, dx, dy) in ((6, 6, 1, 1), (S - 7, 6, -1, 1), (6, S - 7, 1, -1), (S - 7, S - 7, -1, -1)):
        d.line([(x, y), (x + dx * L, y)], fill=ph, width=2); d.line([(x, y), (x, y + dy * L)], fill=ph, width=2)
    return scanlines(img, 3, 0.78)


def terminal_boot(W, H, t, lines, final=None):
    f = ImageFont.truetype(str(F("VT323.ttf")), 22)
    bg, ph = hexrgb(t["bg"]), hexrgb(t["phos"])
    total = sum(len(s) for s in lines); frames = []
    for i in range(8):
        img = solid((W, H), bg); d = ImageDraw.Draw(img)
        budget = int(total * min(1, (i + 1) / 6)); y = 16
        for s in lines:
            shown = s[:max(0, budget)]; budget -= len(s)
            d.text((14, y), shown, font=f, fill=ph); y += 24
        if budget >= 0 and i % 2 == 0: d.rectangle([14, y + 2, 26, y + 20], fill=ph)  # cursor
        if final and i >= 6: final(img, d)
        img = Image.composite(img, solid((W, H), bg), glowm(Image.new("L", (W, H), 255), 0))
        frames.append(q(scanlines(img, 3, 0.75), 12))
    return frames


def waste_boot(W, H, t):
    def thumbs(img, d):
        m = glyph_mask(0xF0513, 70, 90)
        img.paste(solid((90, 90), hexrgb(t["phos"])), (W - 104, H - 104), m)
    return terminal_boot(W, H, t, ["BRUCE INDUSTRIES UNIFIED OS", "COPYRIGHT 2075-2077", "- SERVER 1 -", "",
                                   "> LOGON ADMIN", "PASSWORD: ********", "", "WELCOME, OVERSEER."], thumbs)


# ── 5 versus-fighter ──
FIGHT = dict(bg="120000", text="FFD000", dim="B03020", led="FF3000",
             icons=icons(others=0xF0B65, config=0xF082C, rf=0xF0238))


def fighter_icon(key, S, t):
    img = solid((S, S), (14, 0, 0)); d = ImageDraw.Draw(img)
    for k in range(-2, 6):
        x = k * 34
        d.polygon([(x, S), (x + 16, S), (x + 16 + S, 0), (x + S, 0)], fill=(70, 6, 6))
    m = mask_of(t, key, S, 0.58)
    paint(img, m.filter(ImageFilter.MaxFilter(9)), (0, 0, 0), (4, 5))
    paint(img, m.filter(ImageFilter.MaxFilter(9)), (0, 0, 0))
    img.paste(metal((S, S), hexrgb("FFF200"), hexrgb("FF8C00"), hexrgb("C00000")), (0, 0), m)
    return img


def fighter_boot(W, H, t):
    big = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 64); mid = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 34)
    fire = metal((W, H), hexrgb("FFF200"), hexrgb("FF8C00"), hexrgb("C00000"))
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        d.polygon([(0, 0), (W // 2 + 30, 0), (W // 2 - 30, H), (0, H)], fill=(150, 20, 20))
        d.polygon([(W // 2 + 30, 0), (W, 0), (W, H), (W // 2 - 30, H)], fill=(20, 40, 150))
        slide = max(0, 3 - i) * 50
        d.text((80 - slide, 60), "BRUCE", font=mid, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
        d.text((W - 80 + slide, 60), "CYD", font=mid, fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
        word = "VS" if i < 5 else ("ROUND 1" if i < 6 else "FIGHT!")
        if i >= 2:
            m = text_mask((W, H), (W // 2, 140), word, big)
            paint(img, m.filter(ImageFilter.MaxFilter(9)), (0, 0, 0))
            img.paste(fire, (0, 0), m)
        frames.append(q(img, 32))
    return frames


# ── 6 soul-battle ──
SOUL = dict(bg="000000", text="FFFFFF", dim="FF8C00", led="FF0000", grid=24, icons=icons(others=0xF02D1))
HEART = [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."]


def soul_icon(key, S, t):
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    d.rectangle([6, 6, S - 7, S - 7], outline=(255, 255, 255), width=4)
    g = t["grid"]
    spr = sprite(pixelate(mask_of(t, key, S, 0.5, 0.47), g), (255, 255, 255), (255, 255, 255), (0, 0, 0), g).resize((S, S), Image.NEAREST)
    img.paste(spr, (0, 0), spr)
    draw_bits(d, HEART, S - 30, S - 26, 2, (255, 0, 0))
    return img


def soul_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 10); b = ImageFont.truetype(str(PIXEL), 9)
    msg = "* BRUCE blocks the way!"
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        d.rectangle([20, 110, W - 21, 190], outline=(255, 255, 255), width=4)
        d.text((34, 126), msg[:min(len(msg), (i + 1) * 4)], font=f, fill=(255, 255, 255))
        hx = 150 + int(18 * math.sin(i))
        draw_bits(d, HEART, hx, 160, 3, (255, 0, 0))
        big = ImageFont.truetype(str(PIXEL), 34)
        d.text((W // 2, 50), "BRUCE", font=big, fill=(255, 255, 255), anchor="mm")
        for k, word in enumerate(("FIGHT", "ACT", "ITEM", "SPARE")):
            x = 14 + k * 76
            sel = k == (i // 2) % 4
            d.rectangle([x, 204, x + 66, 230], outline=hexrgb("FF8C00") if not sel else (255, 255, 0), width=2)
            d.text((x + 33, 217), word, font=b, fill=hexrgb("FF8C00") if not sel else (255, 255, 0), anchor="mm")
        frames.append(q(img, 8))
    return frames


# ── 7 vector-rocks ──
VECTOR = dict(bg="000000", text="FFFFFF", dim="808080", led="FFFFFF", icons=icons(others=0xF0463, nrf=0xF0629))


def rock_poly(cx, cy, r, rnd, n=9):
    return [(cx + r * rnd.uniform(0.7, 1.0) * math.cos(k * 2 * math.pi / n), cy + r * rnd.uniform(0.7, 1.0) * math.sin(k * 2 * math.pi / n)) for k in range(n)]


def vector_icon(key, S, t):
    rnd = random.Random("vec-" + key)
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    for _ in range(6): d.point((rnd.randrange(S), rnd.randrange(S)), fill=(160, 160, 160))
    m = mask_of(t, key, S, 0.6)
    paint(img, ring(m, 5), (255, 255, 255))
    return img


def vector_boot(W, H, t):
    f = ImageFont.truetype(str(PIXEL), 38); s = ImageFont.truetype(str(PIXEL), 10)
    rnd = random.Random(2)
    rocks = [(rnd.randrange(W), rnd.randrange(60, H), rnd.randint(12, 28), rnd.uniform(-6, 6), rnd.uniform(-4, 4), random.Random(k)) for k in range(7)]
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        d.text((12, 10), "%05d" % (i * 250), font=s, fill=(255, 255, 255))
        tm = text_mask((W, H), (W // 2, 56), "BRUCE", f)
        paint(img, ring(tm, 3), (255, 255, 255))
        for x, y, r, vx, vy, pr in rocks:
            pts = rock_poly((x + vx * i) % W, (y + vy * i) % H, r, random.Random(pr.random()))
            d.polygon(pts, outline=(255, 255, 255))
        a = i * 0.5
        cx, cy = W // 2, 160
        ship = [(cx + 14 * math.cos(a), cy + 14 * math.sin(a)), (cx + 10 * math.cos(a + 2.5), cy + 10 * math.sin(a + 2.5)),
                (cx + 4 * math.cos(a + math.pi), cy + 4 * math.sin(a + math.pi)), (cx + 10 * math.cos(a - 2.5), cy + 10 * math.sin(a - 2.5))]
        d.polygon(ship, outline=(255, 255, 255))
        for k in range(1, 3): d.point((cx + (14 + k * 14) * math.cos(a), cy + (14 + k * 14) * math.sin(a)), fill=(255, 255, 255))
        frames.append(q(img, 4))
    return frames


# ── 8 speed-rings ──
SPEED = dict(bg="0B2A9E", text="FFFFFF", dim="FFD700", led="1E6BFF", icons=icons(others=0xF046E, rf=0xF140B))


def speed_icon(key, S, t):
    rnd = random.Random("spd-" + key)
    img = metal((S, S), hexrgb("3D8BFF"), hexrgb("1447D6"), hexrgb("0A1A6F")); d = ImageDraw.Draw(img)
    for _ in range(7):
        y = rnd.randrange(8, S - 8); x = rnd.randrange(-20, S // 2)
        d.line([(x, y), (x + rnd.randint(30, 70), y)], fill=(170, 200, 255), width=2)
    c, r = S // 2, int(S * 0.36)
    d.ellipse([c - r, c - r, c + r, c + r], outline=hexrgb("B8860B"), width=9)
    d.ellipse([c - r + 1, c - r + 1, c + r - 1, c + r - 1], outline=hexrgb("FFD700"), width=5)
    m = mask_of(t, key, S, 0.46)
    paint(img, m.filter(ImageFilter.MaxFilter(7)), hexrgb("0A1A6F"))
    paint(img, m, (255, 255, 255))
    return img


def speed_boot(W, H, t):
    f = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 84)
    rnd = random.Random(9)
    lines = [(rnd.randrange(H), rnd.randint(40, 140)) for _ in range(18)]
    frames = []
    for i in range(8):
        img = metal((W, H), hexrgb("3D8BFF"), hexrgb("1447D6"), hexrgb("0A1A6F")); d = ImageDraw.Draw(img)
        for k, (y, L) in enumerate(lines):
            x = (k * 37 - i * 60) % (W + L) - L
            d.line([(x, y), (x + L, y)], fill=(170, 200, 255), width=2)
        for k in range(5):  # spinning rings (ellipse width = rotation)
            cx, w = 40 + k * 60, abs(int(14 * math.cos(i * 0.8 + k)))
            d.ellipse([cx - w - 2, 190, cx + w + 2, 222], outline=hexrgb("FFD700"), width=4)
        x = W // 2 + max(0, 4 - i) * 70
        m = text_mask((W, H), (x, 100), "BRUCE", f)
        m = m.transform((W, H), Image.AFFINE, (1, 0.25, -25, 0, 1, 0))  # italic lean
        paint(img, m.filter(ImageFilter.MaxFilter(9)), hexrgb("0A1A6F"), (4, 5))
        paint(img, m.filter(ImageFilter.MaxFilter(9)), hexrgb("0A1A6F"))
        paint(img, m, (255, 255, 255))
        frames.append(q(img, 32))
    return frames


# ── 9 hacker-mask ──
HACKER = dict(bg="000000", text="FFFFFF", dim="C8102E", led="C8102E",
              icons=icons(others=0xF05F9, interpreter=0xF018D, config=0xF00E4))


def brush(d, box, rnd, col):
    x0, y0, x1, y1 = box; pts = []
    for k in range(14): pts.append((x0 + (x1 - x0) * k / 13, y0 + rnd.randint(-6, 6)))
    for k in range(14): pts.append((x1 - (x1 - x0) * k / 13, y1 + rnd.randint(-6, 6)))
    d.polygon(pts, fill=col)


def hacker_icon(key, S, t):
    rnd = random.Random("hk-" + key)
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    brush(d, (14, 28, S - 14, S - 28), rnd, hexrgb("C8102E"))
    m = mask_of(t, key, S, 0.5)
    paint(img, m.filter(ImageFilter.MaxFilter(5)), (0, 0, 0))
    paint(img, m, (255, 255, 255))
    d.text((8, S - 20), ">_", font=ImageFont.truetype(str(F("VT323.ttf")), 18), fill=(255, 255, 255))
    return img


def hacker_boot(W, H, t):
    tf = title_font(56); f = ImageFont.truetype(str(F("VT323.ttf")), 24)
    rnd = random.Random(13)
    msg = "hello, friend."
    mask = glyph_mask(0xF05F9, 90, 110)
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        brush(d, (40, 90, W - 40, 150), random.Random(3), hexrgb("C8102E"))
        d.text((W // 2, 120), "BRUCE", font=tf, fill=(255, 255, 255), anchor="mm")
        img.paste(solid((110, 110), (255, 255, 255)), (W // 2 - 55, -18), mask)
        d.text((W // 2, 196), msg[:i * 3], font=f, fill=(255, 255, 255), anchor="mm")
        if i < 4:  # glitch slices while it boots
            for _ in range(4 - i):
                y, h = rnd.randrange(H - 10), rnd.randint(3, 14)
                img.paste(img.crop((0, y, W, y + h)), (rnd.randint(-30, 30), y))
        frames.append(q(img, 8))
    return frames


# ── 10 starship-panel ──
PANEL = dict(bg="000000", text="FF9C00", dim="CC99CC", led="FF9C00",
             colors=["FF9C00", "CC99CC", "9999FF", "FFCC99", "CC6666", "99CCFF"],
             icons=icons(others=0xF0463, nrf=0xF0768, interpreter=0xF018D))


def panel_icon(key, S, t):
    idx = MENUS.index(key)
    a, b = hexrgb(t["colors"][idx % 6]), hexrgb(t["colors"][(idx + 2) % 6])
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, S - 4, 26], radius=11, fill=a)            # top bar
    d.rounded_rectangle([4, 4, 26, S - 4], radius=11, fill=a)            # side bar (elbow)
    d.rounded_rectangle([22, 22, 40, 40], radius=9, fill=(0, 0, 0))
    d.rectangle([4, 60, 26, 64], fill=(0, 0, 0))
    d.text((S - 8, 16), "%02d-%d" % (idx + 1, 4700 + idx * 13), font=vfont(F("Antonio.ttf"), 14, 700), fill=(0, 0, 0), anchor="rm")
    m = glyph_mask(t["icons"][key], int(S * 0.46), S, yfrac=0.58)
    img.paste(solid((S, S), b), (10, 4), m)
    return img


def panel_boot(W, H, t):
    f = vfont(F("Antonio.ttf"), 48, 700); s = vfont(F("Antonio.ttf"), 14, 700)
    cols = [hexrgb(x) for x in t["colors"]]
    frames = []
    for i in range(8):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        d.rounded_rectangle([6, 6, 120, 40], radius=17, fill=cols[0]); d.rectangle([60, 6, W - 6, 22], fill=cols[0])
        d.rounded_rectangle([6, 6, 44, H - 6], radius=17, fill=cols[1])
        d.rounded_rectangle([40, 38, 70, 60], radius=11, fill=(0, 0, 0))
        d.text((W - 10, 36), "BRUCE", font=f, fill=cols[0], anchor="ra")
        for k in range(8):  # status blocks light up one by one
            x, y = 60 + (k % 4) * 64, 110 + (k // 4) * 40
            lit = k <= i + 1
            d.rounded_rectangle([x, y, x + 58, y + 32], radius=14, fill=cols[(k + 2) % 6] if lit else (40, 40, 40))
            d.text((x + 52, y + 16), "%d" % (1024 + k * 37), font=s, fill=(0, 0, 0), anchor="rm")
        if i >= 6: d.text((60, 206), "ALL SYSTEMS NOMINAL", font=s, fill=cols[3])
        frames.append(q(img, 16))
    return frames


# ── 11 space-crawl ──
CRAWL = dict(bg="000000", text="FFE81F", dim="4DA6FF", led="FFE81F", icons=icons(others=0xF0463, lora=0xF0471))


def crawl_icon(key, S, t):
    rnd = random.Random("crawl-" + key)
    img = solid((S, S), (0, 0, 0)); d = ImageDraw.Draw(img)
    for _ in range(14): d.point((rnd.randrange(S), rnd.randrange(S)), fill=(rnd.randint(120, 255),) * 3)
    m = mask_of(t, key, S, 0.64)
    m = m.transform((S, S), Image.QUAD, (-S * 0.18, 0, -S * 0.02, S, S * 1.02, S, S * 1.18, 0))  # tilt back
    paint(img, m, hexrgb("FFE81F"))
    return img


def crawl_boot(W, H, t):
    f = vfont(F("Oswald.ttf"), 20, 600); big = vfont(F("Oswald.ttf"), 40, 700); blue = vfont(F("Oswald.ttf"), 17, 400)
    rnd = random.Random(21)
    stars = [(rnd.randrange(W), rnd.randrange(H), rnd.randint(110, 255)) for _ in range(70)]
    text = ["EPISODE CYD", "BRUCE", "It is a period of civil", "hacking. Rebel devices,", "striking from a hidden", "workbench, have won", "their first victory..."]
    frames = []
    for i in range(9):
        img = solid((W, H), (0, 0, 0)); d = ImageDraw.Draw(img)
        for x, y, v in stars: d.point((x, y), fill=(v, v, v))
        if i < 2:
            d.text((W // 2, H // 2 - 12), "Not long ago, on a workbench", font=blue, fill=hexrgb("4DA6FF"), anchor="mm")
            d.text((W // 2, H // 2 + 12), "nearby....", font=blue, fill=hexrgb("4DA6FF"), anchor="mm")
        else:
            page = Image.new("L", (W, 520), 0); pd = ImageDraw.Draw(page)
            y = 250 - (i - 2) * 30
            for k, s in enumerate(text):
                pd.text((W // 2, y), s, font=big if k == 1 else f, fill=255, anchor="mm"); y += 56 if k == 1 else 34
            crawl = page.transform((W, H), Image.QUAD, (W * 0.38, 0, 0, 520, W, 520, W * 0.62, 0), Image.BILINEAR)
            paint(img, crawl, hexrgb("FFE81F"))
        frames.append(q(img, 16))
    return frames


# ── 12 wall-lights ──
WALL = dict(bg="0E0A08", text="E81C1C", dim="8A5A3A", led="FF3B3B",
            bulbs=["FF3030", "30A0FF", "FFD030", "30E060", "FF60E0"], icons=icons(others=0xF0335, rfid=0xF109C))


def wall_icon(key, S, t):
    img = metal((S, S), hexrgb("3A2A1E"), hexrgb("241810"), hexrgb("120C08")); d = ImageDraw.Draw(img)
    pts = [(x, 16 + int(6 * math.sin(x / 14))) for x in range(0, S + 1, 4)]
    d.line(pts, fill=(20, 20, 16), width=2)
    for k, x in enumerate(range(10, S, 22)):  # string of bulbs
        y = 16 + int(6 * math.sin(x / 14)) + 6
        col = hexrgb(t["bulbs"][(k + MENUS.index(key)) % 5])
        img.paste(solid((S, S), col), (0, 0), glowm(text_mask((S, S), (x, y + 3), "●", ImageFont.truetype(NERD, 14)), 4, 1.2))
        d.ellipse([x - 4, y - 1, x + 4, y + 9], fill=col)
    m = mask_of(t, key, S, 0.5, 0.58)
    paint(img, glowm(m, 5, 1.6), (120, 10, 10))
    paint(img, ring(m, 5), hexrgb("FF3B3B"))
    return img


def wall_boot(W, H, t):
    f = vfont(F("LibreBaskerville.ttf"), 50, 700); lf = vfont(F("LibreBaskerville.ttf"), 20, 700)
    rows = ["ABCDEFGH", "IJKLMNOPQ", "RSTUVWXYZ"]
    pos = {}
    for r, row in enumerate(rows):
        for k, ch in enumerate(row):
            pos[ch] = (22 + k * (276 // (len(row) - 1)), 118 + r * 42)
    word = "BRUCE"
    frames = []
    for i in range(9):
        img = metal((W, H), hexrgb("5A4636"), hexrgb("3A2A1E"), hexrgb("1E140C")); d = ImageDraw.Draw(img)
        for ch, (x, y) in pos.items():
            d.line([(x - 16, y - 18), (x + 16, y - 18)], fill=(25, 20, 15), width=2)
            d.text((x, y), ch, font=lf, fill=(20, 16, 12), anchor="mm")
            lit = i < 6 and ch == word[i % 5] and i < 5 or (i >= 6 and ch in word)
            col = hexrgb(t["bulbs"][ord(ch) % 5])
            if lit: img.paste(solid((W, H), col), (0, 0), glowm(text_mask((W, H), (x, y - 16), "●", ImageFont.truetype(NERD, 16)), 6, 1.5))
            d = ImageDraw.Draw(img)
            d.ellipse([x - 4, y - 22, x + 4, y - 12], fill=col if lit else (50, 45, 40))
        if i >= 6:
            m = text_mask((W, H), (W // 2, 56), "BRUCE", f)
            paint(img, glowm(m, 6, 1.6), (150, 10, 10))
            paint(img, ring(m, 5), hexrgb("FF3B3B"))
        frames.append(q(img, 32))
    return frames


# ── 13 time-circuits ──
TIME = dict(bg="1C1C1C", text="FF3030", dim="30FF60", led="FFB000", leds=["FF3030", "30FF60", "FFB000"],
            icons=icons(others=0xF07AC, rf=0xF0241, clock=0xF0152))
SEGS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg"}


def seg_digit(d, x, y, w, h, ch, col, dim):
    tseg = max(2, w // 5)
    rects = {"a": (x, y, x + w, y + tseg), "g": (x, y + h // 2 - tseg // 2, x + w, y + h // 2 + tseg // 2), "d": (x, y + h - tseg, x + w, y + h),
             "f": (x, y, x + tseg, y + h // 2), "b": (x + w - tseg, y, x + w, y + h // 2),
             "e": (x, y + h // 2, x + tseg, y + h), "c": (x + w - tseg, y + h // 2, x + w, y + h)}
    for sname, r in rects.items(): d.rectangle(r, fill=col if sname in SEGS.get(ch, "") else dim)


def time_icon(key, S, t):
    col = cycle(t, key, "leds")
    img = solid((S, S), (40, 40, 40)); d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 24], fill=(70, 70, 70))
    d.text((S // 2, 12), key.upper(), font=vfont(F("Antonio.ttf"), 15, 700), fill=(220, 220, 220), anchor="mm")
    d.rectangle([10, 32, S - 11, S - 11], fill=(8, 8, 8), outline=(90, 90, 90), width=2)
    m = mask_of(t, key, S, 0.46, 0.6)
    paint(img, glowm(m, 5, 1.5), tuple(v // 3 for v in col))
    paint(img, m, col)
    return img


def time_boot(W, H, t):
    lab = vfont(F("Antonio.ttf"), 12, 700); mon = vfont(F("Antonio.ttf"), 26, 700); ttl = vfont(F("Oswald.ttf"), 30, 700)
    rows = [("DESTINATION TIME", "OCT", "26", "1985", "0121"), ("PRESENT TIME", "SEP", "23", "2026", "1958"), ("LAST TIME DEPARTED", "NOV", "05", "1955", "0600")]
    frames = []
    for i in range(8):
        img = solid((W, H), (28, 28, 28)); d = ImageDraw.Draw(img)
        d.text((W // 2, 18), "BRUCE TIME CIRCUITS", font=ttl, fill=(200, 200, 200), anchor="mm")
        for r, (label, mo, dd, yy, hm) in enumerate(rows):
            y = 42 + r * 64
            col = hexrgb(t["leds"][r]); dim = tuple(v // 7 for v in col)
            on = i >= r * 2 + 1 and not (i == r * 2 + 1 and r == 0)
            d.rectangle([6, y, W - 7, y + 58], fill=(12, 12, 12), outline=(90, 90, 90))
            d.rectangle([80, y + 46, 240, y + 58], fill=(70, 70, 70))
            d.text((160, y + 52), label, font=lab, fill=(230, 230, 230), anchor="mm")
            d.text((42, y + 22), mo if on else "", font=mon, fill=col, anchor="mm")
            x = 78
            for k, ch in enumerate(dd + yy + hm):
                seg_digit(d, x, y + 8, 14, 28, ch if on else "", col, dim)
                x += 20 + (8 if k in (1, 5) else 0)
        frames.append(q(img, 16))
    return frames


# ── 14 magic-word: early-90s workstation window, 1-bit ──
MAGIC = dict(bg="FFFFFF", text="000000", dim="808080", led="FF0000", grid=30,
             icons=icons(others=0xF1362, interpreter=0xF018D))


def window_icon(key, S, t):
    img = solid((S, S), (255, 255, 255)); d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], outline=(0, 0, 0), width=2)
    for y in range(6, 20, 3): d.line([(4, y), (S - 5, y)], fill=(0, 0, 0))
    d.rectangle([12, 5, 24, 18], fill=(255, 255, 255), outline=(0, 0, 0))
    d.line([(2, 22), (S - 3, 22)], fill=(0, 0, 0), width=2)
    g = t["grid"]
    spr = sprite(pixelate(mask_of(t, key, S, 0.5, 0.58), g), (0, 0, 0), (0, 0, 0), (255, 255, 255), g).resize((S, S), Image.NEAREST)
    img.paste(spr, (0, 0), spr)
    return img


def magic_boot(W, H, t):
    f = ImageFont.truetype(str(F("VT323.ttf")), 21)
    lines = ["BRUCE Park, System Security Interface", "Version 4.0.5, Alpha E", "Ready...", "> access security",
             "access: PERMISSION DENIED.", "> access main security grid", "access: PERMISSION DENIED....and...."]
    frames = []
    for i in range(9):
        img = solid((W, H), (255, 255, 255)); d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W - 1, 18], fill=(255, 255, 255)); [d.line([(0, y), (W, y)], fill=(0, 0, 0)) for y in range(3, 17, 3)]
        d.text((W // 2, 9), " BRUCE ", font=f, fill=(0, 0, 0), anchor="mm")
        d.line([(0, 19), (W, 19)], fill=(0, 0, 0), width=2)
        for k, s in enumerate(lines[:min(len(lines), i + 1)]): d.text((6, 22 + k * 20), s, font=f, fill=(0, 0, 0))
        if i >= 7:
            for k in range(3): d.text((6, 166 + k * 20), "YOU DIDN'T SAY THE MAGIC WORD!", font=f, fill=(0, 0, 0))
        frames.append(q(img, 2))
    return frames


# ── 15 ghost-zapper ──
ZAP = dict(bg="1B1030", text="B7FF3C", dim="7A5FB0", led="B7FF3C", icons=icons(others=0xF02A0, config=0xF0241))


def zap_icon(key, S, t):
    rnd = random.Random("zap-" + key)
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    m = mask_of(t, key, S, 0.52, 0.45)
    slime = m.filter(ImageFilter.MaxFilter(11))
    sd = ImageDraw.Draw(slime)
    bb = m.getbbox() or (0, 0, S, S)
    for _ in range(3):
        x = rnd.randint(bb[0] + 6, bb[2] - 6); y = bb[3] + 2; ln = rnd.randint(10, 26)
        sd.rounded_rectangle([x - 3, y - 6, x + 3, y + ln], radius=3, fill=255); sd.ellipse([x - 5, y + ln - 4, x + 5, y + ln + 6], fill=255)
    paint(img, glowm(slime, 6, 1.3), (40, 90, 10))
    paint(img, slime, hexrgb("7ED321"))
    paint(img, m, (255, 255, 255))
    return img


def zap_boot(W, H, t):
    f = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 70)
    g = glyph_mask(0xF02A0, 90, 110)
    rnd = random.Random(6)
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        d.rectangle([W // 2 - 30, 206, W // 2 + 30, 226], fill=(160, 160, 160), outline=(40, 40, 40), width=2)  # trap
        d.rectangle([W // 2 - 26, 202, W // 2 + 26, 206], fill=(255, 220, 0) if i >= 5 else (90, 90, 90))
        if i < 6:
            s = 1.0 - max(0, i - 2) * 0.28
            gm = g.resize((max(1, int(110 * s)), max(1, int(110 * s))))
            gx, gy = W // 2 - gm.width // 2, int(60 + max(0, i - 2) * 38)
            paint(img, glowm(Image.new("L", (W, H), 0), 1), (0, 0, 0))
            img.paste(solid(gm.size, (170, 255, 120)), (gx, gy), gm)
            for k in range(2):  # proton streams
                pts = [(0 if k == 0 else W, 230)]
                for step in range(1, 7):
                    x = (0 if k == 0 else W) + (gx + gm.width // 2 - (0 if k == 0 else W)) * step / 6
                    pts.append((x, 230 + (gy + gm.height // 2 - 230) * step / 6 + rnd.randint(-8, 8)))
                d.line(pts, fill=(255, 120, 40), width=4); d.line(pts, fill=(255, 240, 200), width=1)
        if i >= 5:
            m = text_mask((W, H), (W // 2, 90), "BRUCE", f)
            paint(img, m.filter(ImageFilter.MaxFilter(9)), (40, 90, 10))
            paint(img, m, hexrgb("B7FF3C"))
        frames.append(q(img, 24))
    return frames


# ── 16 light-grid ──
GRIDT = dict(bg="00060D", text="6FF6FF", dim="1B6E8A", led="6FF6FF",
             colors=["6FF6FF", "FF9A1F"], icons=icons(others=0xF037C))


def perspective_grid(d, W, H, horizon, col, phase=0.0, spacing=10):
    for k in range(-12, 13):
        d.line([(W / 2 + k * 6, horizon), (W / 2 + k * W / 5, H)], fill=col)
    y, step = horizon, 2.0 + phase * 2
    while y < H:
        d.line([(0, y), (W, y)], fill=col); step *= 1.35; y += step


def grid_icon(key, S, t):
    col = cycle(t, key)
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    perspective_grid(d, S, S, int(S * 0.62), tuple(v // 4 for v in hexrgb("6FF6FF")))
    m = mask_of(t, key, S, 0.5, 0.42)
    r = ring(m, 5)
    paint(img, glowm(r, 5, 2.2), tuple(v // 2 for v in col))
    paint(img, r, col)
    return img


def grid_boot(W, H, t):
    f = vfont(F("Orbitron.ttf"), 56, 900)
    cy, org = hexrgb("6FF6FF"), hexrgb("FF9A1F")
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        perspective_grid(d, W, H, 130, tuple(v // 3 for v in cy), phase=(i % 4) / 4)
        L = min(W, 40 * (i + 1))
        for (y, col, dirn) in ((190, cy, 1), (215, org, -1)):  # light-cycle trails
            x0 = 0 if dirn > 0 else W
            x1 = x0 + dirn * L
            tr = Image.new("L", (W, H), 0); ImageDraw.Draw(tr).line([(x0, y), (x1, y)], fill=255, width=3)
            paint(img, glowm(tr, 4, 2), tuple(v // 2 for v in col)); paint(img, tr, col)
        m = text_mask((W, H), (W // 2, 70), "BRUCE", f)
        k = min(1.0, i / 4)
        paint(img, glowm(m, 7, 1.8 * k), tuple(int(v * 0.45) for v in cy))
        paint(img, ring(m, 3), cy)
        frames.append(q(img, 24))
    return frames


THEMES.update({
    "maze-chomper": (MAZE, maze_icon, maze_boot),
    "block-stack": (STACK, stack_icon, stack_boot),
    "block-craft": (CRAFT, craft_icon, craft_boot),
    "wasteland-terminal": (WASTE, phosphor_icon, waste_boot),
    "versus-fighter": (FIGHT, fighter_icon, fighter_boot),
    "soul-battle": (SOUL, soul_icon, soul_boot),
    "vector-rocks": (VECTOR, vector_icon, vector_boot),
    "speed-rings": (SPEED, speed_icon, speed_boot),
    "hacker-mask": (HACKER, hacker_icon, hacker_boot),
    "starship-panel": (PANEL, panel_icon, panel_boot),
    "space-crawl": (CRAWL, crawl_icon, crawl_boot),
    "wall-lights": (WALL, wall_icon, wall_boot),
    "time-circuits": (TIME, time_icon, time_boot),
    "magic-word": (MAGIC, window_icon, magic_boot),
    "ghost-zapper": (ZAP, zap_icon, zap_boot),
    "light-grid": (GRIDT, grid_icon, grid_boot),
})
PIXEL_STYLE = {"hero-quest", "pixel-plumber", "alien-arcade", "wild-encounter", "maze-chomper", "block-stack",
               "block-craft", "soul-battle", "vector-rocks", "magic-word", "time-circuits"}


# ═════════════════════════ batch 3: gacha / portal cartoon / alien cartoon / 90s couch cartoon ═════════════════════════
GACHA = dict(bg="0D0A24", text="FFD66B", dim="8C7BD6", led="FFD66B",
             rarities=[("FFE9A3", "D4A017", "7A5A00", 5), ("E6C8FF", "A259FF", "4B1E8C", 4), ("C8E6FF", "3E8BFF", "173E80", 3)],
             icons=icons(others=0xF0AE2, config=0xF0B8A, files=0xF0726, rfid=0xF0638))


def star5(d, cx, cy, r, col, outline=None):
    pts = [(cx + (r if k % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5),
            cy + (r if k % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill=col, outline=outline)


def gacha_icon(key, S, t):
    idx = MENUS.index(key)
    light, mid, dark, stars = [hexrgb(c) if isinstance(c, str) else c for c in t["rarities"][0 if idx % 5 == 0 else (1 if idx % 2 else 2)]]
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    card = Image.new("L", (S, S), 0); ImageDraw.Draw(card).rounded_rectangle([14, 6, S - 15, S - 7], radius=10, fill=255)
    img.paste(metal((S, S), light, mid, dark), (0, 0), card)
    d.rounded_rectangle([20, 12, S - 21, S - 13], radius=7, fill=tuple(v // 3 for v in dark))
    d.rounded_rectangle([14, 6, S - 15, S - 7], radius=10, outline=light, width=2)
    m = mask_of(t, key, S, 0.44, 0.44)
    paint(img, glowm(m, 6, 1.4), mid); paint(img, m, (255, 255, 255))
    for k in range(stars):
        star5(d, S // 2 + (k - (stars - 1) / 2) * 15, S - 26, 6, hexrgb("FFD66B"), (90, 60, 0))
    sparkle(d, 26, 22, 6, (255, 255, 255))
    return img


def gacha_boot(W, H, t):
    f = vfont(F("Oswald.ttf"), 34, 700); s = vfont(F("Oswald.ttf"), 16, 600)
    gold = hexrgb("FFD66B")
    frames = []
    for i in range(9):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        for k in range(3):  # summoning circle
            r = 40 + k * 22
            d.ellipse([W // 2 - r * 1.6, 200 - r * 0.4, W // 2 + r * 1.6, 200 + r * 0.4], outline=(120, 90, 220), width=2)
        if 1 <= i <= 4:  # beam of light
            bw = 10 + i * 12
            beam = Image.new("L", (W, H), 0); ImageDraw.Draw(beam).rectangle([W // 2 - bw, 0, W // 2 + bw, 200], fill=255)
            paint(img, glowm(beam, 10, 1.2), (255, 240, 200))
        if i >= 4:  # rainbow glint + card
            for k, col in enumerate(("FF6B9E", "FFD84D", "6EDC8C", "5DBBFF", "A77BFF")):
                a = i * 0.3 + k * 1.25
                d.line([(W // 2, 104), (W // 2 + 170 * math.cos(a), 104 + 170 * math.sin(a))], fill=hexrgb(col), width=3)
            flip = min(1.0, (i - 3) / 3)
            cw = int(110 * flip)
            card = Image.new("L", (W, H), 0); ImageDraw.Draw(card).rounded_rectangle([W // 2 - cw // 2, 30, W // 2 + cw // 2, 178], radius=10, fill=255)
            img.paste(metal((W, H), hexrgb("FFE9A3"), hexrgb("D4A017"), hexrgb("7A5A00")), (0, 0), card)
            d = ImageDraw.Draw(img)
            if flip >= 1:
                d.rounded_rectangle([W // 2 - 48, 38, W // 2 + 48, 170], radius=7, fill=(40, 26, 80))
                d.text((W // 2, 92), "BRUCE", font=f, fill=gold, anchor="mm")
                for k in range(5): star5(d, W // 2 + (k - 2) * 17, 140, 7, gold, (90, 60, 0))
        if i >= 7:
            d.text((W // 2, 222), "SSR GET!", font=s, fill=gold, anchor="mm")
            for x in (W // 2 - 56, W // 2 + 56): star5(d, x, 222, 8, gold, (90, 60, 0))
        frames.append(q(img, 48))
    return frames


PORTAL = dict(bg="14142A", text="B6F24A", dim="6FA3B8", led="3EF000",
              icons=icons(others=0xF124B, nrf=0xF0768, gps=0xF01E7))


def swirl(size, cx, cy, r, turns, phase, cols):
    """Green portal: concentric wobbly swirl bands."""
    img = Image.new("RGBA", size, (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for k in range(int(r), 0, -3):
        a = phase + (r - k) / r * turns * math.pi * 2
        col = cols[(int((r - k) / 3) + int(phase * 3)) % len(cols)]
        ox, oy = 3 * math.cos(a), 3 * math.sin(a)
        d.ellipse([cx - k + ox, cy - k * 0.95 + oy, cx + k + ox, cy + k * 0.95 + oy], fill=col + (255,))
    return img


PORTAL_COLS = [hexrgb(c) for c in ("2D8A12", "3EB51C", "6BD62A", "B6F24A", "E6FF9A", "6BD62A")]


def portal_icon(key, S, t):
    rnd = random.Random("portal-" + key)
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    for _ in range(8): d.point((rnd.randrange(S), rnd.randrange(S)), fill=(200, 200, 230))
    sw = swirl((S, S), S // 2, S // 2, S * 0.44, 1.5, rnd.random() * 6, PORTAL_COLS)
    img.paste(sw, (0, 0), sw)
    m = mask_of(t, key, S, 0.46)
    paint(img, m.filter(ImageFilter.MaxFilter(9)), (20, 30, 20)); paint(img, m, (255, 255, 255))
    return img


def portal_boot(W, H, t):
    f = ImageFont.truetype(str(F("Fredoka.ttf")), 70); f.set_variation_by_axes([700, 100])
    s = ImageFont.truetype(str(F("Fredoka.ttf")), 16); s.set_variation_by_axes([600, 100])
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        r = min(110, 20 + i * 22)
        sw = swirl((W, H), W // 2, H // 2, r, 2, i * 0.7, PORTAL_COLS)
        img.paste(sw, (0, 0), sw)
        if i >= 4:
            m = text_mask((W, H), (W // 2, H // 2), "BRUCE", f)
            wob = Image.new("L", (W, H), 0)
            for x in range(0, W, 4):  # wobble: shift each 4px column up/down on a sine
                wob.paste(m.crop((x, 0, x + 4, H)), (x, int(5 * math.sin(x / 26 + i))))
            m = wob
            paint(img, m.filter(ImageFilter.MaxFilter(11)), (20, 60, 10)); paint(img, m, hexrgb("B6F24A"))
        if i >= 6: d.text((W // 2, 222), "*burp* ...let's go.", font=s, fill=(230, 255, 200), anchor="mm")
        frames.append(q(img, 32))
    return frames


IRK = dict(bg="0A0008", text="FF2E9E", dim="8A2A6A", led="FF2E9E",
           icons=icons(others=0xF089A, config=0xF06A9, nrf=0xF10C4))


def hexgrid(d, W, H, r, col, width=1):
    h = r * math.sqrt(3)
    for row in range(-1, int(H / h) + 2):
        for colx in range(-1, int(W / (r * 1.5)) + 2):
            cx = colx * r * 1.5; cy = row * h + (h / 2 if colx % 2 else 0)
            d.polygon([(cx + r * math.cos(k * math.pi / 3), cy + r * math.sin(k * math.pi / 3)) for k in range(6)], outline=col, width=width)


def irk_icon(key, S, t):
    rnd = random.Random("irk-" + key)
    img = solid((S, S), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
    hexgrid(d, S, S, 14, (60, 0, 40))
    m = mask_of(t, key, S, 0.54)
    paint(img, glowm(m, 7, 1.8), (140, 0, 80))
    paint(img, m, hexrgb("FF2E9E"))
    paint(img, ImageChops.subtract(m, m.filter(ImageFilter.MinFilter(5))), (255, 190, 225))
    for _ in range(3):
        x, y = rnd.randrange(10, S - 10), rnd.randrange(10, S - 10)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=(255, 30, 30))
    return img


def irk_boot(W, H, t):
    f = vfont(F("Orbitron.ttf"), 54, 900); s = vfont(F("Orbitron.ttf"), 15, 700)
    pink = hexrgb("FF2E9E")
    rnd = random.Random(12)
    traces = [[(rnd.randrange(W), rnd.randrange(H))] for _ in range(10)]
    for tr in traces:
        for _ in range(5):
            x, y = tr[-1]
            tr.append((x + rnd.choice([-1, 1]) * rnd.randint(15, 50), y) if len(tr) % 2 else (x, y + rnd.choice([-1, 1]) * rnd.randint(15, 40)))
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        hexgrid(d, W, H, 18, (45, 0, 30))
        for tr in traces:  # circuits power up segment by segment
            seg = tr[:min(len(tr), i + 1)]
            if len(seg) > 1: d.line(seg, fill=(160, 20, 100), width=2); d.ellipse([seg[-1][0] - 3, seg[-1][1] - 3, seg[-1][0] + 3, seg[-1][1] + 3], fill=pink)
        if i >= 3:
            m = text_mask((W, H), (W // 2, 104), "BRUCE", f)
            paint(img, glowm(m, 8, 1.8), (120, 0, 70)); paint(img, m, pink)
        if i >= 5: d.text((W // 2, 160), "ALL HAIL BRUCE", font=s, fill=(255, 60, 60), anchor="mm")
        frames.append(q(img, 24))
    return frames


COUCH = dict(bg="1E2A6E", text="FFE14D", dim="8FA6FF", led="FFE14D",
             panels=["FFE14D", "4DB8FF", "FF7A3D", "7ED957"],
             icons=icons(others=0xF07F4, fm=0xF02C4, config=0xF0238))


def scribble(d, mask, rnd, col, passes=2, width=3):
    """Hand-drawn marker outline: jittered traces around the mask edge."""
    edge = ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(3)), mask).point(lambda v: 255 if v > 60 else 0)
    W, H = mask.size
    px = edge.load()
    for _ in range(passes):
        jx, jy = rnd.uniform(-2, 2), rnd.uniform(-2, 2)
        for y in range(0, H, 2):
            for x in range(0, W, 2):
                if px[x, y]: d.ellipse([x + jx - width / 2, y + jy - width / 2, x + jx + width / 2, y + jy + width / 2], fill=col)


def couch_icon(key, S, t):
    rnd = random.Random("couch-" + key)
    img = solid((S, S), cycle(t, key, "panels")); d = ImageDraw.Draw(img)
    for _ in range(5):  # loose marker hatching
        x = rnd.randrange(-20, S)
        d.line([(x, S), (x + 30, S - 30)], fill=tuple(max(0, v - 30) for v in cycle(t, key, "panels")), width=3)
    m = mask_of(t, key, S, 0.56)
    paint(img, m, (255, 255, 255))
    scribble(d, m, rnd, (20, 20, 20), passes=2, width=4)
    d.rectangle([2, 2, S - 3, S - 3], outline=(20, 20, 20), width=3)
    return img


def couch_boot(W, H, t):
    f = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 58); s = ImageFont.truetype(str(F("Bangers-Regular.ttf")), 22)
    rnd = random.Random(1)
    frames = []
    for i in range(8):
        img = solid((W, H), hexrgb(t["bg"])); d = ImageDraw.Draw(img)
        d.rounded_rectangle([40, 30, 280, 190], radius=18, fill=(90, 60, 40), outline=(20, 20, 20), width=4)  # TV cabinet
        d.rounded_rectangle([58, 46, 232, 174], radius=14, fill=(30, 30, 30), outline=(20, 20, 20), width=3)
        for k in range(3): d.ellipse([246, 60 + k * 36, 266, 80 + k * 36], fill=(200, 180, 120), outline=(20, 20, 20), width=2)
        d.line([(120, 30), (90, 4)], fill=(20, 20, 20), width=3); d.line([(180, 30), (214, 2)], fill=(20, 20, 20), width=3)
        if i < 4:  # static
            for _ in range(700):
                x, y = rnd.randrange(62, 229), rnd.randrange(50, 171)
                v = rnd.choice((40, 200, 255)); d.rectangle([x, y, x + 2, y + 1], fill=(v, v, v))
        else:
            m = text_mask((W, H), (145, 110), "BRUCE", f)
            paint(img, m, hexrgb("FFE14D"))
            scribble(ImageDraw.Draw(img), m, random.Random(i), (20, 20, 20), passes=1, width=3)
        d = ImageDraw.Draw(img)
        d.rectangle([20, 196, W - 20, H - 6], fill=(60, 40, 30), outline=(20, 20, 20), width=3)  # couch
        if i >= 6: d.text((W // 2, 216), "heh heh. this rocks.", font=s, fill=(255, 255, 255), anchor="mm", stroke_width=2, stroke_fill=(20, 20, 20))
        frames.append(q(img, 24))
    return frames


THEMES.update({
    "gacha-pull": (GACHA, gacha_icon, gacha_boot),
    "dimension-hop": (PORTAL, portal_icon, portal_boot),
    "tiny-invader": (IRK, irk_icon, irk_boot),
    "couch-critics": (COUCH, couch_icon, couch_boot),
})


def littlefs_image(theme_dir, name, size=0x30000, block=4096):
    """Build a LittleFS image holding the theme + a bruce.conf selecting it. Returns (bytes, used_blocks) or None if full."""
    from littlefs import LittleFS, errors
    fs = LittleFS(block_size=block, block_count=size // block, name_max=64, disk_version=0x00020000)
    try:
        fs.mkdir(f"/{name}")
        for p in sorted(theme_dir.iterdir()):
            with fs.open(f"/{name}/{p.name}", "wb") as fh: fh.write(p.read_bytes())
        th = json.loads((theme_dir / f"{name}.json").read_text())
        conf = {k: th[k] for k in ("priColor", "secColor", "bgColor")}
        conf.update(themeFile=f"/{name}/{name}.json", themeOnSd=1)
        with fs.open("/bruce.conf", "w") as fh: fh.write(json.dumps(conf))
    except errors.LittleFSError:
        return None
    return bytes(fs.context.buffer), fs.used_block_count


MIN_FREE = 5  # Bruce adds brucePins.conf + rewrites bruce.conf and wants >4 KB spare
# JPG settings tried in order until the theme fits the CYD's 192 KB LittleFS
QUALITY_STEPS = [(90, 0), (85, 2), (78, 2), (70, 2), (62, 2), (55, 2)]


def build(name, a):
    t, icon_fn, boot_fn = THEMES[name]
    W, H, S = 320, 240, 132
    out = a.out / name
    out.mkdir(parents=True, exist_ok=True)
    icons_img = {key: icon_fn(key, S, t).convert("RGB") for key in MENUS}
    frames = boot_fn(W, H, t)
    frames[0].save(out / "boot.gif", save_all=True, append_images=frames[1:],
                   duration=[140] * (len(frames) - 1) + [1500], loop=1, optimize=True)
    theme = {k: f"{k}.jpg" for k in MENUS}
    theme.update(priColor=rgb565(hexrgb(t["text"])), secColor=rgb565(hexrgb(t["dim"])), bgColor=rgb565(hexrgb(t["bg"])),
                 border=1, label=1, boot_img="boot.gif", ledBright=60, ledColor=t["led"], ledEffect=0,
                 ledEffectSpeed=3, ledEffectDirection=1)
    (out / f"{name}.json").write_text(json.dumps(theme, indent=2) + "\n")
    steps = QUALITY_STEPS if name in PIXEL_STYLE else QUALITY_STEPS[1:]
    img = None
    for qual, sub in steps:
        for key, im in icons_img.items(): im.save(out / f"{key}.jpg", quality=qual, subsampling=sub)
        img = littlefs_image(out, name)
        if img and 48 - img[1] >= MIN_FREE: break
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
    boot_kb = (out / "boot.gif").stat().st_size / 1024
    if not img or 48 - img[1] < MIN_FREE:
        print(f"{name}: {kb:.0f} KB (boot {boot_kb:.0f} KB)  !! does NOT fit the CYD LittleFS even at q{qual}; SD card only")
        return False
    print(f"{name}: {kb:.0f} KB (boot {boot_kb:.0f} KB), icons q{qual}, {img[1]}/48 blocks")
    if a.littlefs: (ROOT / "local" / f"{name}-littlefs.bin").write_bytes(img[0])
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help=", ".join(THEMES))
    ap.add_argument("--out", type=Path, default=ROOT / "pop")
    ap.add_argument("--littlefs", action="store_true")
    a = ap.parse_args()
    for n in a.names or THEMES:
        if n not in THEMES: sys.exit(f"unknown theme '{n}'")
        try:
            build(n, a)
        except Exception as e:  # keep going so one broken theme doesn't stop a batch
            import traceback; traceback.print_exc(); print(f"{n}: FAILED ({e})")


if __name__ == "__main__":
    main()
