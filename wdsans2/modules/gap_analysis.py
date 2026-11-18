#!/usr/bin/env python3
"""gap_analysis - OPPO/HOS 缺口中哪些是「SHS也没有且真需要」的"""
from fontTools.ttLib import TTFont

paths = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS": "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS": "/workspace/wdsans/ref/hos/hos-400.ttf",
    "Mona": "/workspace/wdsans/ref/mona/MonaSansVF.ttf",
}
cm = {}
for n, p in paths.items():
    f = TTFont(p, lazy=True)
    cm[n] = set(f.getBestCmap().keys())
    f.close()

ours = cm["我们"]
# OPPO 或 HOS 有、我们没有
union = cm["OPPO"] | cm["HOS"]
gap = union - ours
print("OPPO∪HOS 有而我们缺: %d" % len(gap))

# 其中 SHS 也没有的（说明不是我们漏了，是上游本来没有）
notshs = gap - cm["SHS"]
print("  其中 SHS 也没有: %d" % len(notshs))
print()

# 按区块
BLOCKS = [
    ("Latin-1 Sup", 0x00A0, 0x00FF),
    ("Latin Ext-A", 0x0100, 0x017F),
    ("Latin Ext-B", 0x0180, 0x024F),
    ("IPA", 0x0250, 0x02AF),
    ("Spacing Mod", 0x02B0, 0x02FF),
    ("Comb Diacrit", 0x0300, 0x036F),
    ("Greek", 0x0370, 0x03FF),
    ("Cyrillic", 0x0400, 0x04FF),
    ("Cyrillic Sup", 0x0500, 0x052F),
    ("Gen Punct", 0x2000, 0x206F),
    ("Super/Sub", 0x2070, 0x209F),
    ("Currency", 0x20A0, 0x20CF),
    ("Letterlike", 0x2100, 0x214F),
    ("Number Forms", 0x2150, 0x218F),
    ("Arrows", 0x2190, 0x21FF),
    ("Math Ops", 0x2200, 0x22FF),
    ("Enclosed", 0x2460, 0x24FF),
    ("Box Drawing", 0x2500, 0x257F),
    ("Geometric", 0x25A0, 0x25FF),
    ("Misc Sym", 0x2600, 0x26FF),
    ("CJK Sym", 0x3000, 0x303F),
    ("Hangul Compat", 0x3130, 0x318F),
]
from collections import defaultdict
byb = defaultdict(list)
oth = []
for cp in sorted(notshs):
    for bn, lo, hi in BLOCKS:
        if lo <= cp <= hi:
            byb[bn].append(cp); break
    else:
        oth.append(cp)

print("=== SHS 也没有的缺口（按区块，含 Mona 是否可供）===")
mona = cm["Mona"]
for bn, lo, hi in BLOCKS:
    if bn in byb:
        lst = byb[bn]
        avail = sum(1 for c in lst if c in mona)
        s = "".join(chr(c) for c in lst[:40])
        print("%-14s %3d  其中Mona可供 %d  %s" % (bn, len(lst), avail, s))
if oth:
    print("%-14s %3d  其中Mona可供 %d" % ("其他", len(oth), sum(1 for c in oth if c in mona)))
print()
print("合计: SHS也没有的缺口 %d，其中 Mona 可供 %d" % (len(notshs), sum(1 for c in notshs if c in mona)))
