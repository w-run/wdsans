#!/usr/bin/env python3
"""probe_reclaim - 找可回收的 glyph 槽位"""
from fontTools.ttLib import TTFont
VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap()
order = f.getGlyphOrder()
cs = f["CFF2"].cff.topDictIndex[0].CharStrings
mapped = set(cm.values())
print("numGlyphs = %d" % f["maxp"].numGlyphs)
print("glyphOrder 长度 = %d" % len(order))
print("cmap 映射的 glyph 数 = %d" % len(mapped))
unmapped = [g for g in order if g not in mapped]
print("未映射 glyph 数 = %d" % len(unmapped))

print()
print("=== 未映射 glyph 是否被 GSUB/GPOS 引用 ===")
refs = set()
if "GSUB" in f:
    for lk in f["GSUB"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if st is None: continue
            d = getattr(st, "mapping", None)
            if isinstance(d, dict):
                refs.update(d.keys()); refs.update(d.values())
            cov = getattr(st, "Coverage", None)
            if cov is not None:
                refs.update(cov.glyphs or [])
if "GPOS" in f:
    for lk in f["GPOS"].table.LookupList.Lookup:
        for st in lk.SubTable:
            if st is None: continue
            cov = getattr(st, "Coverage", None)
            if cov is not None:
                refs.update(cov.glyphs or [])

free = [g for g in unmapped if g not in refs]
print("既未映射、又未被 GSUB/GPOS 引用: %d 个" % len(free))
if free:
    print("  前 10 个: %s" % free[:10])

# 检查这些 glyph 是否有实际轮廓（空轮廓最安全）
gs = f.getGlyphSet()
from fontTools.pens.boundsPen import BoundsPen
empty = []
for g in free[:200]:
    bp = BoundsPen(gs)
    try:
        gs[g].draw(bp)
    except Exception:
        empty.append(g); continue
    if bp.bounds is None:
        empty.append(g)
print()
print("其中空轮廓（可安全复用）: %d / 检查了 %d 个" % (len(empty), min(200, len(free))))
if empty:
    print("  样例: %s" % empty[:5])
f.close()