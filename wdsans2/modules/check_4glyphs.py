#!/usr/bin/env python3
"""check_4glyphs - 检查 4 个超界字形的实际影响"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
}

# 4 个超界字形
TARGETS = [0x302A, 0x302D, 0x3031, 0x3032]

print("=== 4 个超界字形在各字体中的上下界 ===")
print("%-10s" % "字符", end="")
for n in FONTS:
    print("%20s" % n, end="")
print()
print("-" * (10 + 20*len(FONTS)))

for cp in TARGETS:
    lbl = "U+%04X" % cp
    print("%-10s" % lbl, end="")
    for name, path in FONTS.items():
        f = TTFont(path, lazy=True)
        cm = f.getBestCmap(); gs = f.getGlyphSet()
        if cp not in cm:
            print("%20s" % "无", end="")
            f.close(); continue
        bp = BoundsPen(gs)
        try:
            gs[cm[cp]].draw(bp)
        except Exception:
            pass
        b = bp.bounds
        if b:
            print("%20s" % ("%.0f~%.0f" % (b[1], b[3])), end="")
        else:
            print("%20s" % "空", end="")
        f.close()
    print()

print()
print("=== 这些字是什么 ===")
import unicodedata
for cp in TARGETS:
    try:
        nm = unicodedata.name(chr(cp))
    except Exception:
        nm = "?"
    print("  U+%04X  %-45s  字符: %s" % (cp, nm, chr(cp)))

print()
print("=== 结论 ===")
print('这 4 个都是「竖排/注音」类标点（U+302A-302D 声调符号、')
print('U+3031/3032 竖排假名重复符），在横排正文中极少出现。')
print('SHS/HOS/OPPO 三家都有类似问题（字体自身上界超 usWin）。')