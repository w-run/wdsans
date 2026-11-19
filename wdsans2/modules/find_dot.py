#!/usr/bin/env python3
"""find_dot - 找字体里已有的、尺寸合适的圆点字形"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet(); h = f['hmtx']

# 各种圆点类字符（目标墨迹 ~230，advance ~500）
CANDS = [
    (0x25CF, "BLACK CIRCLE ●"),
    (0x25CB, "WHITE CIRCLE ○"),
    (0x26AB, "MEDIUM BLACK CIRCLE ⚫"),
    (0x2B24, "BLACK LARGE CIRCLE ⬤"),
    (0x25AA, "BLACK SMALL SQUARE ▪"),
    (0x25FE, "BLACK MEDIUM SMALL SQUARE ◾"),
    (0x2981, "Z NOTATION SPOT ⦁"),
    (0xFE61, "SMALL ASTERISK ﹡"),
    (0x204C, "BLACK LEFTWARDS BULLET ⁌"),
    (0x2219, "BULLET OPERATOR ∙"),
    (0x22C5, "DOT OPERATOR ⋅"),
]

print("%-32s %-14s %10s %10s" % ("字符", "glyph", "墨迹", "advance"))
print("-" * 70)
for cp, name in CANDS:
    if cp not in cm:
        print("%-32s 字体无此字符" % name);
        continue
    gn = cm[cp]
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        pass
    b = bp.bounds
    if b:
        print("%-32s %-14s %4.0fx%-4.0f %10d" % (name, gn, b[2]-b[0], b[3]-b[1], h[gn][0]))
    else:
        print("%-32s %-14s 无墨 %10d" % (name, gn, h[gn][0]))

print()
print("目标: 墨迹接近 230x230，advance 接近 500")
f.close()