#!/usr/bin/env python3
"""check_middot - 量化间隔号 · 的问题"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}
CHARS = ["\u00b7", "\u2022", "\u30fb"]  # · 间隔号 / • 项目符号 / ・片假名中点
NAMES = {"\u00b7": "U+00B7 ·", "\u2022": "U+2022 •", "\u30fb": "U+30FB ・"}

print("=== 1. advance width（字体设计值）===")
print("%-6s" % "字体", end="")
for c in CHARS: print("%12s" % NAMES[c], end="")
print()
for name, path in FONTS.items():
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap(); hmtx = f["hmtx"]; upm = f["head"].unitsPerEm
    row = "%-6s" % name
    for c in CHARS:
        cp = ord(c)
        if cp in cm:
            gn = cm[cp]
            aw = hmtx[gn][0]
            row += "%12s" % ("%d u" % aw)
        else:
            row += "%12s" % "无"
    f.close()
    print(row)

print()
print("=== 2. 渲染墨迹宽度与两侧留白（400px）===")
SZ = 400
def ink_and_adv(path, ch):
    ft = ImageFont.truetype(path, SZ)
    # 单字渲染
    img = Image.new("L", (SZ*3, SZ*3), 0)
    ImageDraw.Draw(img).text((SZ, SZ), ch, fill=255, font=ft)
    a = np.array(img) > 128
    c = np.where(a.any(axis=0))[0]
    if not len(c): return None, None
    ink_w = c[-1] - c[0] + 1
    try:
        adv = ft.getlength(ch)
    except Exception:
        adv = None
    return ink_w, adv

print("%-6s %10s %10s %10s %10s" % ("字体", "墨宽", "advance", "左留白", "右留白"))
for name, path in FONTS.items():
    iw, adv = ink_and_adv(path, "\u00b7")
    if iw is None:
        print("%-6s 无 · 字形" % name); continue
    left = (adv - iw) / 2
    print("%-6s %10d %10.1f %10.1f %10.1f" % (name, iw, adv, left, left))

print()
print("=== 3. 实际混排：设置·消息 ===")
def render_text(path, text, px=SZ):
    ft = ImageFont.truetype(path, px)
    img = Image.new("L", (px*len(text)+200, px*3), 0)
    ImageDraw.Draw(img).text((50, px), text, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return c[-1]-c[0]+1 if len(c) else 0

for name, path in FONTS.items():
    w = render_text(path, "设置\u00b7消息")
    print("  %-5s 「设置·消息」总宽 %d" % (name, w))
