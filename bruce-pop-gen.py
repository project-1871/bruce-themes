#!/usr/bin/env python3
"""Generate pop-culture-styled Bruce firmware themes, each with its own art style.

  p-cat          cute stickers: white-outlined candy-pink icons, sparkles, bubbly boot title with a bow
  hero-quest     8-bit pixel art: gold/green/blue sprites on a dark forest, heart-meter boot
  pixel-plumber  8-bit pixel art: bright sprites on sky blue, brick ground + ? blocks boot
  code-rain      green katakana code rain behind glowing icons, rain resolves into the title

Inspired by classic pop culture. All art is drawn here from generic icon glyphs and shapes:
no official artwork, sprites or logos.

Usage: ./bruce-pop-gen.py [p-cat hero-quest pixel-plumber code-rain] [--littlefs]
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


THEMES = {
    "p-cat": (PCAT, pcat_icon, pcat_boot),
    "hero-quest": (HERO, lambda k, S, t: pixel_icon(k, S, t, "hero"), hero_boot),
    "pixel-plumber": (PLUMBER, lambda k, S, t: pixel_icon(k, S, t, "plumber"), plumber_boot),
    "code-rain": (RAIN, rain_icon, rain_boot),
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
    pixel = name in ("hero-quest", "pixel-plumber")
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
