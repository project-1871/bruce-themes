#!/usr/bin/env python3
"""Generate dripping monster-style Bruce firmware themes.

Every menu gets a monster symbol with a glow and slime drips, and the boot
screen is a dripping BRUCE title in the Creepster horror font.

Examples:
  ./bruce-monster-gen.py                     # build every monster in MONSTERS -> monster/<name>/
  ./bruce-monster-gen.py vampire slime       # just these
  ./bruce-monster-gen.py vampire --littlefs  # + flashable LittleFS image
"""
import argparse, json, random, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
NERD_FONTS = ["/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf",
              str(Path.home() / ".local/share/fonts/JetBrainsMonoNerdFont-Regular.ttf")]
HORROR_FONT = ROOT / "fonts" / "Creepster-Regular.ttf"

# Bruce menu -> monster symbol (Material Design glyphs in Nerd Fonts)
ICONS = {
    "wifi": 0xF0BCA,         # spider_web: the web you tap into
    "ble": 0xF0B5F,          # bat: short-range flyer
    "rf": 0xF043C,           # radioactive
    "rfid": 0xF14C7,         # skull_scan
    "fm": 0xF02A0,           # ghost: voices on the radio
    "ir": 0xF0208,           # eye: sees what you can't
    "files": 0xF0BA2,        # grave_stone: where things are buried
    "gps": 0xF0B2F,          # crystal_ball: finds you anywhere
    "nrf": 0xF089A,          # alien
    "interpreter": 0xF1132,  # bottle_tonic_skull: scripts are potions
    "clock": 0xF05E2,        # candle: time burning down
    "lora": 0xF03D2,         # owl: sees far in the dark
    "others": 0xF0BBF,       # pumpkin
    "connect": 0xF11EA,      # spider
    "config": 0xF1844,       # magic_staff
}

# name: (background, body/text, dim text, drip, glow)
MONSTERS = {
    "slime":        ("0E140A", "B6FF3B", "6F8F3A", "7CFF00", "2E5A00"),
    "vampire":      ("12060A", "F2E6E6", "8C6E72", "C0001F", "5A0010"),
    "werewolf":     ("0D0F16", "D9DEE8", "7A8296", "D0922C", "2A3350"),
    "frankenstein": ("0F1410", "9FD39A", "5E7A5B", "E8F000", "3B5A3A"),
    "mummy":        ("17120B", "E8D9B0", "8F8468", "C9A227", "5A4520"),
    "ghost":        ("0A0F14", "DFF6FF", "7D93A0", "7FD8FF", "1F4D66"),
    "kraken":       ("061216", "7FE3D8", "4A8580", "9B5CFF", "12404A"),
    "pumpkin":      ("100A05", "FF8A1F", "94602E", "FFD23F", "5A2A00"),
    "witch":        ("120A18", "C9A8FF", "7A6699", "6AFF6A", "3A1F5A"),
    "zombie":       ("12140F", "B9C4A0", "6E7560", "9E1B1B", "3A3F2A"),
}


def hexrgb(s): return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgb565(c):
    r, g, b = c
    return format(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3), "x")


def font(paths, size):
    for p in map(str, paths):
        if Path(p).exists(): return ImageFont.truetype(p, size)
    sys.exit(f"font not found: {paths}")


def drips(mask, rnd, count, max_len, width):
    """Draw drips hanging from the lowest edges of a mask, as a new mask."""
    W, H = mask.size
    px = mask.load()
    bottoms = []
    for x in range(W):
        ys = [y for y in range(H - 1, -1, -1) if px[x, y] > 128]
        if ys: bottoms.append((x, ys[0]))
    out = Image.new("L", mask.size, 0)
    if not bottoms: return out
    d = ImageDraw.Draw(out)
    lowest = max(b for _, b in bottoms)
    spots = [(x, y) for x, y in bottoms if y > lowest - H * 0.18] or bottoms
    used = []
    for _ in range(count * 4):
        if len(used) >= count: break
        x, y = rnd.choice(spots)
        if any(abs(x - u) < width * 2.2 for u in used): continue
        used.append(x)
        w = rnd.randint(max(2, width - 2), width + 1)
        ln = rnd.randint(max_len // 3, max_len)
        d.rounded_rectangle([x - w // 2, y - w, x + w // 2, min(H - 3, y + ln)], radius=w // 2, fill=255)
        r = w // 2 + 2  # fat droplet at the tip
        cy = min(H - r - 1, y + ln)
        d.ellipse([x - r, cy - r, x + r, cy + r], fill=255)
    return out


def glow(mask, radius, strength=2.2):
    g = mask.filter(ImageFilter.GaussianBlur(radius))
    return g.point(lambda v: min(255, int(v * strength)))


def make_icon(key, cp, gfont, S, bg, fg, drip_c, glow_c):
    rnd = random.Random("monster-" + key)
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    bb = d.textbbox((0, 0), chr(cp), font=gfont)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((S - w) // 2 - bb[0], int(S * 0.44) - h // 2 - bb[1]), chr(cp), font=gfont, fill=255)
    dm = drips(m, rnd, 3, int(S * 0.28), max(4, S // 22))
    body = Image.new("L", (S, S), 0)
    body.paste(m, (0, 0)); body.paste(255, (0, 0), dm)
    img = Image.new("RGB", (S, S), bg)
    img.paste(Image.new("RGB", (S, S), glow_c), (0, 0), glow(body, S // 16))
    img.paste(Image.new("RGB", (S, S), drip_c), (0, 0), dm)
    img.paste(Image.new("RGB", (S, S), fg), (0, 0), m)
    return img


def make_boot(W, H, name, bg, fg, drip_c, glow_c, dim):
    title_f, sub_f = font([HORROR_FONT], int(H * 0.36)), font([HORROR_FONT], int(H * 0.11))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((W // 2, int(H * 0.42)), "BRUCE", font=title_f, fill=255, anchor="mm")
    rnd = random.Random("boot-" + name)
    full = drips(m, rnd, 7, int(H * 0.30), max(5, W // 45))
    frames, n = [], 9
    for i in range(n):
        grow = min(1.0, (i + 1) / (n - 2))
        # reveal drips from the top down as they "run"
        cut = Image.new("L", (W, H), 0)
        ImageDraw.Draw(cut).rectangle([0, 0, W, int(H * 0.42 + H * 0.45 * grow)], fill=255)
        dm = Image.composite(full, Image.new("L", (W, H), 0), cut)
        body = Image.new("L", (W, H), 0); body.paste(m, (0, 0)); body.paste(255, (0, 0), dm)
        f = Image.new("RGB", (W, H), bg)
        f.paste(Image.new("RGB", (W, H), glow_c), (0, 0), glow(body, 7, 1.6 + grow))
        f.paste(Image.new("RGB", (W, H), drip_c), (0, 0), dm)
        f.paste(Image.new("RGB", (W, H), fg), (0, 0), m)
        if i >= n - 3:
            ImageDraw.Draw(f).text((W // 2, int(H * 0.86)), name.upper(), font=sub_f, fill=dim, anchor="mm")
        frames.append(f.quantize(32, dither=Image.Dither.NONE))
    return frames


def build_littlefs(theme_dir, name, out, size, block=4096):
    try:
        from littlefs import LittleFS
    except ImportError:
        sys.exit("--littlefs needs littlefs-python:  pip install littlefs-python")
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


def build(name, pal, a):
    bg, fg, dim, drip_c, glow_c = map(hexrgb, pal)
    W, H = map(int, a.screen.lower().split("x"))
    S = int(H * 0.55)
    out = a.out / name
    out.mkdir(parents=True, exist_ok=True)
    gfont = font(NERD_FONTS, int(S * 0.62))
    for key, cp in ICONS.items():
        make_icon(key, cp, gfont, S, bg, fg, drip_c, glow_c).save(out / f"{key}.jpg", quality=85, subsampling=2)
    frames = make_boot(W, H, name, bg, fg, drip_c, glow_c, dim)
    frames[0].save(out / "boot.gif", save_all=True, append_images=frames[1:],
                   duration=[120] * (len(frames) - 1) + [1500], loop=1, optimize=True)
    theme = {k: f"{k}.jpg" for k in ICONS}
    theme.update(priColor=rgb565(fg), secColor=rgb565(dim), bgColor=rgb565(bg), border=1, label=1,
                 boot_img="boot.gif", ledBright=60, ledColor=pal[3], ledEffect=0, ledEffectSpeed=3,
                 ledEffectDirection=1)
    (out / f"{name}.json").write_text(json.dumps(theme, indent=2) + "\n")

    prev = ROOT / "previews" / "monster"
    prev.mkdir(parents=True, exist_ok=True)
    sheet = Image.new("RGB", (5 * (S + 10) + 10, 3 * (S + 10) + 10), (0, 0, 0))
    for i, key in enumerate(ICONS):
        sheet.paste(Image.open(out / f"{key}.jpg"), (10 + (i % 5) * (S + 10), 10 + (i // 5) * (S + 10)))
    sheet.save(prev / f"{name}-icons.png")
    frames[-1].convert("RGB").save(prev / f"{name}-boot.png")
    frames[0].save(prev / f"{name}-boot.gif", save_all=True, append_images=frames[1:],
                   duration=[120] * (len(frames) - 1) + [1500], loop=0, optimize=True)
    kb = sum(p.stat().st_size for p in out.iterdir()) / 1024
    print(f"{name}: {out}/ ({kb:.0f} KB)")
    if a.littlefs:
        build_littlefs(out, name, ROOT / "local" / f"{name}-littlefs.bin", a.fs_size)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*", help=f"monsters to build (default: all): {', '.join(MONSTERS)}")
    ap.add_argument("--out", type=Path, default=ROOT / "monster")
    ap.add_argument("--screen", default="320x240")
    ap.add_argument("--littlefs", action="store_true", help="also build local/<name>-littlefs.bin")
    ap.add_argument("--fs-size", type=lambda s: int(s, 0), default=0x30000)
    a = ap.parse_args()
    for n in a.names or MONSTERS:
        if n not in MONSTERS: sys.exit(f"unknown monster '{n}'")
        build(n, MONSTERS[n], a)


if __name__ == "__main__":
    main()
