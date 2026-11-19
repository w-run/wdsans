#!/usr/bin/env python3
"""probe_gdef - 检查 GDEF mark class 现状"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
gd = f["GDEF"].table

print("=== GDEF 结构 ===")
print("  GlyphClassDef: %s" % (gd.GlyphClassDef is not None))
print("  MarkAttachClassDef: %s" % (gd.MarkAttachClassDef is not None))
print("  MarkGlyphSetsDef: %s" % (gd.MarkGlyphSetsDef is not None))

if gd.GlyphClassDef:
    cd = gd.GlyphClassDef.classDefs
    print("  分类数量: %d 个 glyph" % len(cd))
    from collections import Counter
    c = Counter(cd.values())
    print("  class 1(base)=%d  class 2(lig)=%d  class 3(mark)=%d  class 4(comp)=%d" % (
        c.get(1,0), c.get(2,0), c.get(3,0), c.get(4,0)))

print()
print("=== 检查 fontbakery 报告的字符是否在 mark class ===")
cm = f.getBestCmap()
MARKS = [0x0323, 0x0309, 0x0303, 0x0302, 0x0304, 0x0306, 0x0308, 0x030A, 0x030B, 0x0312,
         0x20DD, 0x20DE]
cd = gd.GlyphClassDef.classDefs if gd.GlyphClassDef else {}
in_mark = not_in = 0
for cp in MARKS:
    if cp not in cm: continue
    gn = cm[cp]
    cls = cd.get(gn)
    tag = {1:'base', 2:'lig', 3:'mark', 4:'comp'}.get(cls, '未分类')
    flag = 'OK' if cls == 3 else '!!'
    if cls == 3: in_mark += 1
    else: not_in += 1
    print("  %s U+%04X %-16s class=%s" % (flag, cp, gn, tag))

print()
print("  在 mark class: %d   不在: %d" % (in_mark, not_in))

print()
print("=== 全部组合符号检查（0x300-0x36F）===")
comb = [c for c in cm if 0x300 <= c <= 0x36F]
n_mark = sum(1 for c in comb if cd.get(cm[c]) == 3)
n_none = sum(1 for c in comb if cm[c] not in cd)
print("  组合符号 %d 个: 已标 mark %d / 未分类 %d" % (len(comb), n_mark, n_none))

print()
print("=== SHS 对照 ===")
g = TTFont("/workspace/wdsans/ref/shs/shs-400.otf", lazy=True)
gg = g["GDEF"].table
if gg.GlyphClassDef:
    gc = gg.GlyphClassDef.classDefs
    from collections import Counter
    c2 = Counter(gc.values())
    print("  SHS: base=%d lig=%d mark=%d comp=%d" % (
        c2.get(1,0), c2.get(2,0), c2.get(3,0), c2.get(4,0)))
g.close()
f.close()