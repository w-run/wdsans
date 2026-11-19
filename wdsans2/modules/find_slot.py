#!/usr/bin/env python3
"""find_slot - 找一个最安全的可覆写槽位"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); order = f.getGlyphOrder()
cs = f["CFF2"].cff.topDictIndex[0].CharStrings
gs = f.getGlyphSet()
mapped = set(cm.values())

refs = set()
if "GSUB" in f:
    for lk in f["GSUB"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if st is None: continue
            d = getattr(st, "mapping", None)
            if isinstance(d, dict):
                refs.update(d.keys()); refs.update(d.values())
            cov = getattr(st, "Coverage", None)
            if cov is not None: refs.update(cov.glyphs or [])
if "GPOS" in f:
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if st is None: continue
            cov = getattr(st, "Coverage", None)
            if cov is not None: refs.update(cov.glyphs or [])

cands = [g for g in order if g not in mapped and g not in refs and g != '.notdef']
print("候选槽位: %d 个" % len(cands))

# 选那些轮廓是「小尺寸」的（越小越可能是废弃占位）
scored = []
for g in cands[:3000]:
    bp = BoundsPen(gs)
    try:
        gs[g].draw(bp)
    except Exception:
        continue
    b = bp.bounds
    if b is None:
        scored.append((0, g)); continue
    area = (b[2]-b[0]) * (b[3]-b[1])
    scored.append((area, g))

scored.sort()
print("轮廓面积最小的 10 个:")
for a, g in scored[:10]:
    print("  %-16s area=%.0f" % (g, a))

# 推荐用第 1 个（最小）
if scored:
    pick = scored[0][1]
    print()
    print("推荐覆写: %s (area=%.0f)" % (pick, scored[0][0]))
f.close()