#!/usr/bin/env python3
"""Rebuild the gallery GIFs and the README theme tables for every collection."""
import json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = Path(__file__).parent
FRINGE = {"japglitch": "C921E4,2090E3", "hypr-heels": "F5003E,A91DFE"}  # manual overrides used for glitch builds


def names_in(d):
    return sorted(p.name for p in (ROOT / d).iterdir() if (p / f"{p.name}.json").exists())


def gallery(names, prev_dir, out, cols=4, tw=200, th=150):
    rows = -(-len(names) // cols)
    font = ImageFont.load_default(size=13)
    anims = [[f.convert("RGB").resize((tw, th)) for f in ImageSequence.Iterator(Image.open(prev_dir / f"{n}-boot.gif"))]
             for n in names]
    frames = []
    for i in range(max(len(a) for a in anims)):
        g = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 24) + 6), (8, 8, 10))
        d = ImageDraw.Draw(g)
        for k, (n, a) in enumerate(zip(names, anims)):
            x, y = 6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 24)
            g.paste(a[min(i, len(a) - 1)], (x, y))
            d.text((x + tw // 2, y + th + 10), n, fill=(220, 220, 220), font=font, anchor="mm")
        frames.append(g.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE))
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=[110] * (len(frames) - 1) + [1800], loop=0, optimize=True)


def rgb565_to_hex(v):
    v = int(v, 16); r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return "%02X%02X%02X" % (r * 255 // 31, g * 255 // 63, b * 255 // 31)


def sw(h): return f"![](https://placehold.co/12x12/{h}/{h}.png)"


def table(names, theme_dir, prev):
    rows = ["| Theme | Icons | Text / dim / bg | LED |", "|---|---|---|---|"]
    for n in names:
        t = json.loads((ROOT / theme_dir / n / f"{n}.json").read_text())
        c = " ".join(sw(rgb565_to_hex(t[k])) for k in ("priColor", "secColor", "bgColor"))
        rows.append(f"| **`{n}`**<br><sub>[boot]({prev}/{n}-boot.gif)</sub> | <img src=\"{prev}/{n}-icons.png\" width=\"420\"> "
                    f"| {c}<br><sub>`{t['priColor']}` `{t['secColor']}` `{t['bgColor']}`</sub> | {sw(t['ledColor'])} |")
    return "\n".join(rows)


def replace(readme, tag, body):
    return re.sub(rf"(<!-- {tag}:start -->).*?(<!-- {tag}:end -->)", lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}",
                  readme, flags=re.S)


glitch, monster = names_in("themes"), names_in("monster")
gallery(glitch, ROOT / "previews", ROOT / "previews" / "gallery.gif")
gallery(monster, ROOT / "previews" / "monster", ROOT / "previews" / "monster" / "gallery.gif", cols=5, tw=160, th=120)

build = "\n".join(f"./bruce-theme-gen.py {n:<20}" + (f" --fringe {FRINGE[n]}" if n in FRINGE else "") + " --littlefs"
                  for n in glitch)
glitch_md = f"""{table(glitch, "themes", "previews")}

> `auto-wallpaper` is Omarchy's wallust theme that re-colors itself from the current wallpaper, so its Bruce version is a snapshot.

<details>
<summary><b>Exact build commands</b></summary>

```bash
{build}
```
</details>"""

readme = (ROOT / "README.md").read_text()
readme = replace(readme, "glitch", glitch_md)
readme = replace(readme, "monster", table(monster, "monster", "previews/monster"))
readme = re.sub(r"`\d+ themes`", f"`{len(glitch) + len(monster)} themes`", readme)
readme = re.sub(r"(## ▌Glitch collection )\(\d+\)", rf"\g<1>({len(glitch)})", readme)
readme = re.sub(r"(## ▌Monster collection )\(\d+\)", rf"\g<1>({len(monster)})", readme)
(ROOT / "README.md").write_text(readme)
print(f"{len(glitch)} glitch + {len(monster)} monster themes")
