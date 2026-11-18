#!/usr/bin/env python3
"""mona_gap - Mona 有但我们缺的字符（合规可补）"""
import sys
from fontTools.ttLib import TTFont

OURS = "/workspace/static/wdsans/WDesignSans-VF.otf"
MONA = "/workspace/wdsans/ref/mona/MonaSansVF.ttf"

fo = TTFont(OURS, lazy=True)
ours = set(fo.getBestCmap().keys())
print("我们 cmap: %d, glyphs: %d" % (len(ours), fo["maxp"].numGlyphs))
fo.close()

fm = TTFont(MONA, lazy=True)
mona = set(fm.getBestCmap().keys())
print("Mona cmap: %d" % len(mona))
fm.close()

gap = sorted(mona - ours)
print("Mona 有我们缺: %d" % len(gap))
print()

# 按区块归类
BLOCKS = [
    ("Basic Latin", 0x0020, 0x007E),
    ("Latin-1 Sup", 0x00A0, 0x00FF),
    ("Latin Ext-A", 0x0100, 0x017F),
    ("Latin Ext-B", 0x0180, 0x024F),
    ("IPA", 0x0250, 0x02AF),
    ("Spacing Mod", 0x02B0, 0x02FF),
    ("Comb Diacrit", 0x0300, 0x036F),
    ("Greek", 0x0370, 0x03FF),
    ("Cyrillic", 0x0400, 0x04FF),
    ("Latin Ext Add", 0x1E00, 0x1EFF),
    ("Gen Punct", 0x2000, 0x206F),
    ("Super/Sub", 0x2070, 0x209F),
    ("Currency", 0x20A0, 0x20CF),
    ("Letterlike", 0x2100, 0x214F),
    ("Number Forms", 0x2150, 0x218F),
    ("Arrows", 0x2190, 0x21FF),
    ("Math Ops", 0x2200, 0x22FF),
]
from collections import defaultdict
byblock = defaultdict(list)
other = []
for cp in gap:
    found = False
    for bname, lo, hi in BLOCKS:
        if lo <= cp <= hi:
            byblock[bname].append(cp)
            found = True
            break
    if not found:
        other.append(cp)

print("=== 缺口按区块 ===")
for bname, lo, hi in BLOCKS:
    if bname in byblock:
        lst = byblock[bname]
        s = "".join(chr(c) for c in lst)
        print("%-14s %3d  %s" % (bname, len(lst), s))
if other:
    print("%-14s %3d  %s" % ("其他", len(other), "".join(chr(c) for c in other if c < 0x10000)))
