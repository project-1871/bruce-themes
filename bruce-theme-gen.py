#!/usr/bin/env python3
"""Generate a glitch-style Bruce firmware theme from an Omarchy theme palette.

Examples:
  ./bruce-theme-gen.py japglitch                       # -> themes/japglitch/
  ./bruce-theme-gen.py neon-unix-legs --littlefs       # + flashable LittleFS image
  ./bruce-theme-gen.py japglitch --sd --boot-wallpaper # PNG icons + wallpaper boot anim for microSD
  ./bruce-theme-gen.py --colors path/to/colors.toml --name mytheme
"""
import argparse, colorsys, json, os, random, re, sys
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont

OMARCHY_THEMES = [Path.home() / ".config/omarchy/themes", Path.home() / ".local/share/omarchy/themes"]
NERD_FONTS = ["/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Regular.ttf",
              "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf",
              str(Path.home() / ".local/share/fonts/JetBrainsMonoNerdFont-Regular.ttf")]
TITLE_FONTS = [str(Path.home() / ".local/share/fonts/MrRobot.ttf"),
               "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"]

# Bruce main-menu key -> Material Design Nerd Font glyph
ICONS = {
    "wifi": 0xF05A9,         # md-wifi
    "ble": 0xF00AF,          # md-bluetooth
    "rf": 0xF043B,           # md-radio_tower
    "rfid": 0xF0396,         # md-nfc
    "fm": 0xF0439,           # md-radio
    "ir": 0xF0454,           # md-remote
    "files": 0xF024B,        # md-folder
    "gps": 0xF01A4,          # md-crosshairs_gps
    "nrf": 0xF0003,          # md-access_point
    "interpreter": 0xF0169,  # md-code_braces
    "clock": 0xF0150,        # md-clock_outline
    "lora": 0xF1119,         # md-antenna
    "others": 0xF15FC,       # md-dots_grid
    "connect": 0xF0318,      # md-lan_connect
    "config": 0xF0493,       # md-cog
}


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgb565(c):
    r, g, b = c
    return format(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3), "x")


def load_palette(path):
    pal = {k: hexrgb(v) for k, v in re.findall(r'^(\w+)\s*=\s*"(#[0-9A-Fa-f]{6})"', path.read_text(), re.M)}
    missing = {"background", "foreground", "accent"} - pal.keys()
    if missing:
        sys.exit(f"{path}: missing {', '.join(sorted(missing))}")
    return pal


def pick_fringes(pal):
    """Two vivid, well-separated hues for the RGB-split effect, avoiding the icon (foreground) hue."""
    def hsv(c): return colorsys.rgb_to_hsv(*(x / 255 for x in c))
    def huedist(a, b): d = abs(hsv(a)[0] - hsv(b)[0]); return min(d, 1 - d)
    fg = pal["foreground"]
    cands = [pal[k] for k in (f"color{i}" for i in range(1, 15)) if k in pal] + [pal["accent"]]
    cands = [c for c in set(cands) if hsv(c)[1] > 0.35 and (hsv(fg)[1] < 0.2 or huedist(c, fg) > 0.08)] or cands
    vivid = sorted(set(cands), key=lambda c: hsv(c)[1] * hsv(c)[2], reverse=True)[:8]
    best, score = (vivid[0], vivid[-1]), -1
    for a in vivid:
        for b in vivid:
            s = huedist(a, b) * hsv(a)[1] * hsv(a)[2] * hsv(b)[1] * hsv(b)[2]
            if s > score: best, score = (a, b), s
    return best


def first_font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    sys.exit(f"No usable font found in: {paths}")


def make_icon(name, cp, font, S, bg, fg, fringes, bars):
    rnd = random.Random(name)
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    bb = d.textbbox((0, 0), chr(cp), font=font)
    d.text(((S - (bb[2] - bb[0])) // 2 - bb[0], (S - (bb[3] - bb[1])) // 2 - bb[1]), chr(cp), font=font, fill=255)
    img = Image.new("RGB", (S, S), bg)
    for col, dx in zip(fringes, (-S // 26, S // 26)):
        img.paste(Image.new("RGB", (S, S), col), (0, 0), ImageChops.offset(m, dx, 0))
    img.paste(Image.new("RGB", (S, S), fg), (0, 0), m)
    for _ in range(4):  # displaced horizontal slices
        y, h = rnd.randint(10, S - 20), rnd.randint(3, 9)
        dx = rnd.choice([-1, 1]) * rnd.randint(6, 16)
        band = img.crop((0, y, S, y + h)); img.paste(bg, (0, y, S, y + h)); img.paste(band, (dx, y))
    d = ImageDraw.Draw(img)
    for _ in range(2):  # accent glitch blocks
        x, y = rnd.randint(0, S - 30), rnd.randint(0, S - 6)
        d.rectangle([x, y, x + rnd.randint(8, 26), y + 2], fill=rnd.choice(bars))
    return img


def make_boot(W, H, bg, fg, fringes, bars, title_font, wallpaper=None):
    if wallpaper:
        wp = Image.open(wallpaper).convert("RGB")
        sc = max(W / wp.width, H / wp.height)
        wp = wp.resize((round(wp.width * sc), round(wp.height * sc)))
        l, t = (wp.width - W) // 2, (wp.height - H) // 2
        base = wp.crop((l, t, l + W, t + H))
        band = Image.blend(base.crop((0, H // 2 - 45, W, H // 2 + 45)), Image.new("RGB", (W, 90), bg), 0.85)
        base.paste(band, (0, H // 2 - 45))
    else:
        base = Image.new("RGB", (W, H), bg)
        bd = ImageDraw.Draw(base)
        shade = tuple(max(0, c - 8) for c in bg)
        for y in range(0, H, 3): bd.line([(0, y), (W, y)], fill=shade)
        for (fx, fy, fw), c in zip(((0.06, 0.17, 0.28), (0.62, 0.24, 0.22), (0.12, 0.79, 0.19), (0.72, 0.73, 0.16)), bars * 2):
            bd.rectangle([int(fx * W), int(fy * H), int((fx + fw) * W), int(fy * H) + 3], fill=c)
    rnd, frames, n = random.Random(7), [], 8
    for i in range(n):
        f = base.copy(); d = ImageDraw.Draw(f)
        k = 0 if i >= 6 else (6 - i) * 2
        for col, dx in zip(fringes, (-2 - k, 2 + k)):
            d.text((W // 2 + dx, H // 2), "BRUCE", font=title_font, fill=col, anchor="mm")
        d.text((W // 2, H // 2), "BRUCE", font=title_font, fill=fg, anchor="mm")
        for _ in range(max(0, 6 - i)):
            y, h = rnd.randint(0, H - 10), rnd.randint(2, 12)
            f.paste(f.crop((0, y, W, y + h)), (rnd.randint(-25, 25), y))
        frames.append(f.quantize(64 if wallpaper else 24, dither=Image.Dither.NONE))
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
    conf.update(themeFile=f"/{name}/{name}.json", themeOnSd=1)  # 1 = LittleFS, 2 = SD
    with fs.open("/bruce.conf", "w") as fh: fh.write(json.dumps(conf))
    out.write_bytes(fs.context.buffer)
    free = (size // block) - fs.used_block_count
    print(f"LittleFS image: {out}  ({fs.used_block_count}/{size // block} blocks used, {free} free)")
    if free < 3:
        print("  warning: Bruce reports 'LittleFS is Full' below 4 KB free; shrink the theme")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("theme", nargs="?", help="Omarchy theme name (from ~/.config/omarchy/themes)")
    ap.add_argument("--colors", type=Path, help="explicit colors.toml instead of a theme name")
    ap.add_argument("--name", help="output theme name (default: theme name)")
    ap.add_argument("--out", type=Path, default=Path("themes"), help="output root (default: ./themes)")
    ap.add_argument("--fringe", help="override the RGB-split colors, e.g. C921E4,2090E3")
    ap.add_argument("--screen", default="320x240", help="device resolution WxH (default 320x240, CYD)")
    ap.add_argument("--icon-size", type=int, help="icon px (default: 55%% of screen height, 75%% with --no-label)")
    ap.add_argument("--no-label", action="store_true", help="hide menu names, use bigger icons")
    ap.add_argument("--sd", action="store_true", help="target microSD: PNG icons (sharper, needs cache space)")
    ap.add_argument("--boot-wallpaper", nargs="?", const="auto", help="use the theme wallpaper behind the boot title")
    ap.add_argument("--littlefs", nargs="?", const="auto", help="also build a flashable LittleFS image")
    ap.add_argument("--fs-size", type=lambda s: int(s, 0), default=0x30000, help="LittleFS partition size (default 0x30000, CYD)")
    a = ap.parse_args()

    if a.colors:
        colors, name = a.colors, a.name or a.colors.parent.name
    elif a.theme:
        tdir = next((d / a.theme for d in OMARCHY_THEMES if (d / a.theme / "colors.toml").exists()), None)
        if not tdir: sys.exit(f"theme '{a.theme}' not found in {', '.join(map(str, OMARCHY_THEMES))}")
        colors, name = tdir / "colors.toml", a.name or a.theme
    else:
        ap.error("give a theme name or --colors")

    pal = load_palette(colors)
    W, H = map(int, a.screen.lower().split("x"))
    S = a.icon_size or int(H * (0.75 if a.no_label else 0.55))
    bg, fg = pal["background"], pal["foreground"]
    sec = pal.get("color8", tuple((f + b) // 2 for f, b in zip(fg, bg)))
    fringes = tuple(hexrgb(c) for c in a.fringe.split(",")) if a.fringe else pick_fringes(pal)
    print("fringe colors: " + ", ".join("#%02X%02X%02X" % c for c in fringes))
    bars = [pal[k] for k in ("border1", "border2", "border3", "accent") if k in pal]

    out = a.out / name
    out.mkdir(parents=True, exist_ok=True)
    ext = "png" if a.sd else "jpg"
    icon_font = first_font(NERD_FONTS, int(S * 0.74))
    for key, cp in ICONS.items():
        img = make_icon(key, cp, icon_font, S, bg, fg, fringes, bars)
        if ext == "png": img.save(out / f"{key}.png", optimize=True)
        else: img.save(out / f"{key}.jpg", quality=85, subsampling=2)

    wallpaper = None
    if a.boot_wallpaper == "auto":
        bgs = sorted((colors.parent / "backgrounds").glob("*.*"))
        wallpaper = bgs[0] if bgs else None
        if not wallpaper: print("no wallpaper found in theme, using plain boot background")
    elif a.boot_wallpaper:
        wallpaper = a.boot_wallpaper
    frames = make_boot(W, H, bg, fg, fringes, bars, first_font(TITLE_FONTS, int(H * 0.27)), wallpaper)
    frames[0].save(out / "boot.gif", save_all=True, append_images=frames[1:],
                   duration=[110] * (len(frames) - 1) + [1500], loop=1, optimize=True)

    theme = {k: f"{k}.{ext}" for k in ICONS}
    theme.update(priColor=rgb565(fg), secColor=rgb565(sec), bgColor=rgb565(bg), border=1,
                 label=0 if a.no_label else 1, boot_img="boot.gif", ledBright=60,
                 ledColor="%02X%02X%02X" % fringes[0], ledEffect=0, ledEffectSpeed=3, ledEffectDirection=1)
    (out / f"{name}.json").write_text(json.dumps(theme, indent=2) + "\n")

    sheet = Image.new("RGB", (5 * (S + 10) + 10, 3 * (S + 10) + 10), (0, 0, 0))
    for i, key in enumerate(ICONS):
        sheet.paste(Image.open(out / f"{key}.{ext}"), (10 + (i % 5) * (S + 10), 10 + (i // 5) * (S + 10)))
    prev = a.out.parent / "previews" if a.out.name == "themes" else a.out
    prev.mkdir(parents=True, exist_ok=True)
    sheet.save(prev / f"{name}-icons.png")
    frames[-1].convert("RGB").save(prev / f"{name}-boot.png")
    frames[0].save(prev / f"{name}-boot.gif", save_all=True, append_images=frames[1:],
                   duration=[110] * (len(frames) - 1) + [1500], loop=0, optimize=True)

    total = sum(p.stat().st_size for p in out.iterdir())
    print(f"{name}: {out}/  ({total / 1024:.0f} KB, {S}px {ext} icons, "
          f"pri={theme['priColor']} sec={theme['secColor']} bg={theme['bgColor']})")
    if a.littlefs:
        build_littlefs(out, name, Path(a.littlefs if a.littlefs != "auto" else f"{name}-littlefs.bin"), a.fs_size)


if __name__ == "__main__":
    main()
