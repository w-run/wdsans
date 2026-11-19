#!/usr/bin/env python3
"""verify_r35 - R35 完整验证"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont

R35 = "/workspace/wdsans2/build/VF_R35.otf"
R34 = "/workspace/wdsans2/build/VF_R34_backup.otf"
SZ = 64

print("=== 1. advance 对比（核心指标）===")
f = TTFont(R35, lazy=True); cm = f.getBestCmap(); h = f["hmtx"]
g = TTFont(R34, lazy=True); cm2 = g.getBestCmap(); h2 = g["hmtx"]
for cp, name in ((0x00B7,"· U+00B7"), (0x2022,"• U+2022"), (0x2027,"‣ U+2027"), (0x30FB,"・ U+30FB")):
    gn = cm.get(cp); gn2 = cm2.get(cp)
    a = h[gn][0] if gn else -1
    b = h2[gn2][0] if gn2 else -1
    print("  %-12s R34 %4d -> R35 %4d  %s" % (name, b, a, "OK" if a==500 else "!!"))
f.close(); g.close()

print()
print("=== 2. 其他标点未受影响 ===")
f = TTFont(R35, lazy=True); cm = f.getBestCmap(); h = f["hmtx"]
for cp, name in ((0x3001,"、"),(0x3002,"。"),(0xFF0C,"，"),(0xFF1A,"："),(0x2014,"—"),(0x2026,"…")):
    gn = cm.get(cp)
    print("  %-4s adv=%d" % (name, h[gn][0] if gn else -1))
f.close()

print()
print("=== 3. cmap/glyph 数不变 ===")
f = TTFont(R35, lazy=True)
print("  glyphs=%d cmap=%d cjk=%d" % (
    f["maxp"].numGlyphs, len(f.getBestCmap()),
    len([c for c in f.getBestCmap() if 0x4E00<=c<=0x9FFF])))
f.close()

print()
print("=== 4. 渲染间距实测（400px）===")
def width(path, text, px=400):
    ft = ImageFont.truetype(path, px)
    img = Image.new("L", (px*len(text)+300, px*3), 0)
    ImageDraw.Draw(img).text((50, px), text, fill=255, font=ft)
    a = np.array(img) > 128
    c = np.where(a.any(axis=0))[0]
    return c[-1]-c[0]+1 if len(c) else 0

HOS = "/workspace/wdsans/ref/hos/hos-400.ttf"
for txt in ("设置·消息", "A·B"):
    print("  「%s」:" % txt)
    for nm, p in (("R34",R34), ("R35",R35), ("HOS",HOS)):
        print("    %-4s %d px" % (nm, width(p, txt)))
