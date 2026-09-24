#!/usr/bin/env python3
"""Rebuild previews/gallery.gif and the README theme gallery from themes/*/."""
import json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageSequence

FRINGE = {"japglitch": "C921E4,2090E3", "hypr-heels": "F5003E,A91DFE"}  # manual overrides used for builds
root = Path(__file__).parent
names = sorted(p.name for p in (root / "themes").iterdir() if (p / f"{p.name}.json").exists())

# animated 4-column grid of every boot animation
cols, tw, th = 4, 200, 150
rows = -(-len(names) // cols)
font = ImageFont.load_default(size=13)
anims = [[f.convert("RGB").resize((tw, th)) for f in ImageSequence.Iterator(Image.open(root / "previews" / f"{n}-boot.gif"))] for n in names]
frames = []
for i in range(max(len(a) for a in anims)):
    g = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 24) + 6), (8, 8, 10))
    d = ImageDraw.Draw(g)
    for k, (n, a) in enumerate(zip(names, anims)):
        x, y = 6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 24)
        g.paste(a[min(i, len(a) - 1)], (x, y))
        d.text((x + tw // 2, y + th + 10), n, fill=(220, 220, 220), font=font, anchor="mm")
    frames.append(g.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE))
frames[0].save(root / "previews" / "gallery.gif", save_all=True, append_images=frames[1:],
               duration=[110] * (len(frames) - 1) + [1800], loop=0, optimize=True)

def rgb565_to_hex(v):
    v = int(v, 16); r, g, b = (v >> 11) & 31, (v >> 5) & 63, v & 31
    return "%02X%02X%02X" % (r * 255 // 31, g * 255 // 63, b * 255 // 31)

def sw(h): return f"![](https://placehold.co/12x12/{h}/{h}.png)"

rows_md = ["| Theme | Icons | Text / dim / bg | LED |", "|---|---|---|---|"]
for n in names:
    t = json.loads((root / "themes" / n / f"{n}.json").read_text())
    cols_ = " ".join(sw(rgb565_to_hex(t[k])) for k in ("priColor", "secColor", "bgColor"))
    rows_md.append(f"| **`{n}`**<br><sub>[boot](previews/{n}-boot.gif)</sub> | <img src=\"previews/{n}-icons.png\" width=\"420\"> "
                   f"| {cols_}<br><sub>`{t['priColor']}` `{t['secColor']}` `{t['bgColor']}`</sub> | {sw(t['ledColor'])} |")
build = "\n".join(f"./bruce-theme-gen.py {n:<20}" + (f" --fringe {FRINGE[n]}" if n in FRINGE else "") + " --littlefs" for n in names)
section = f"""## ▌Themes ({len(names)})

Every theme is built from the Omarchy theme with the same name. Colors are Bruce RGB565 values.

{chr(10).join(rows_md)}

> `auto-wallpaper` is Omarchy's wallust theme that re-colors itself from the current wallpaper, so its Bruce version is a snapshot.

<details>
<summary><b>Exact build commands</b></summary>

```bash
{build}
```
</details>

"""
readme = (root / "README.md").read_text()
readme = re.sub(r"## ▌Themes.*?(?=---\n\n## ▌Install)", lambda m: section, readme, flags=re.S)
(root / "README.md").write_text(readme)
print(len(names), "themes;", (root / "previews/gallery.gif").stat().st_size // 1024, "KB gallery")
