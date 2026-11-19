#!/usr/bin/env python3
"""probe_layout_order - 找出布局表里未排序的标签"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)

def check_sorted(tags, label):
    if tags == sorted(tags):
        return 0
    bad = []
    for i in range(1, len(tags)):
        if tags[i-1] > tags[i]:
            bad.append((i-1, tags[i-1], tags[i]))
    print("  %s 未排序 (%d 处逆序):" % (label, len(bad)))
    for i, a, b in bad[:6]:
        print("    [%d] %s > %s" % (i, a, b))
    return len(bad)

total = 0
print("=== GSUB ===")
if 'GSUB' in f:
    gs = f['GSUB'].table
    if gs.FeatureList:
        tags = [fr.FeatureTag for fr in gs.FeatureList.FeatureRecord]
        print("  FeatureList %d 个" % len(tags))
        total += check_sorted(tags, "GSUB FeatureList")
    if gs.ScriptList:
        st = [sr.ScriptTag for sr in gs.ScriptList.ScriptRecord]
        total += check_sorted(st, "GSUB ScriptList")
    if gs.LookupList:
        print("  LookupList %d 个（无标签，不需排序）" % len(gs.LookupList.Lookup))

print()
print("=== GPOS ===")
if 'GPOS' in f:
    gp = f['GPOS'].table
    if gp.FeatureList:
        tags = [fr.FeatureTag for fr in gp.FeatureList.FeatureRecord]
        print("  FeatureList %d 个" % len(tags))
        total += check_sorted(tags, "GPOS FeatureList")
        print("  实际顺序: %s" % tags)
    if gp.ScriptList:
        st = [sr.ScriptTag for sr in gp.ScriptList.ScriptRecord]
        total += check_sorted(st, "GPOS ScriptList")

print()
print("=== GDEF ===")
if 'GDEF' in f and f['GDEF'].table.MarkGlyphSetsDef:
    print('  有 MarkGlyphSetsDef')

print("总逆序数: %d" % total)
f.close()