"""三字体并排对照图（hb-view + PIL 拼版）。

设计决策必须先看图：数值只能证明「没坏」，不能证明「好看」。
"""
from __future__ import annotations
import os
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

FONTS = [
    ("Noto（基座）", "/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf", True),
    ("OPPO（主参照）", "/workspace/wdsans/ref/ops/ops-400.ttf", False),
    ("HOS（次参照）", "/workspace/wdsans/ref/hos/hos-400.ttf", False),
]


def render(path, text, size, wght=None, out=None):
    cmd = ["hb-view", f"--font-file={path}", f"--font-size={size}",
           f"--output-file={out}", text]
    if wght is not None:
        cmd.insert(3, f"--variations=wght={wght}")
    subprocess.run(cmd, check=True)
    return out


def build(chars, size, out, wght=400, label="WDesign Sans 参照对照"):
    rows = []
    tmp = tempfile.mkdtemp()
    for name, path, is_var in FONTS:
        p = os.path.join(tmp, f"{name[:4]}-{size}.png")
        try:
            render(path, chars, size, wght if is_var else None, p)
            rows.append((name, Image.open(p).convert("RGB")))
        except Exception as e:
            print(f"  跳过 {name}: {e}")

    pad = 16
    labelw = 190
    w = max(im.width for _, im in rows) + labelw + pad * 2
    h = sum(im.height for _, im in rows) + pad * (len(rows) + 1)
    sheet = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/mona-sans/MonaSans-Regular.ttf", 18)
    except Exception:
        fnt = ImageFont.load_default()
    y = pad
    for name, im in rows:
        sheet.paste(im, (labelw + pad, y))
        d.text((pad, y + im.height // 2 - 10), name, fill="#333", font=fnt)
        y += im.height + pad
    sheet.save(out)
    print("wrote", out, sheet.size)
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("chars")
    ap.add_argument("--size", type=int, default=96)
    ap.add_argument("--wght", type=int, default=400)
    ap.add_argument("--out", default="/tmp/glow/cmp.png")
    a = ap.parse_args()
    build(a.chars, a.size, a.out, a.wght)