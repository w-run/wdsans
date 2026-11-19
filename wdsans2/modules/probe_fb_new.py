#!/usr/bin/env python3
"""probe_fb_new - 核实新发现的 FAIL/WARN"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
SHS = "/workspace/wdsans/ref/shs/shs-400.otf"
f = TTFont(VF, lazy=True)

print("=== FAIL: no_mac_entries（name 表 Mac 记录）===")
nm = f['name']
from collections import Counter
c = Counter((r.platformID, r.platEncID, r.langID) for r in nm.names)
for k, v in sorted(c.items()):
    print("  platform=%d enc=%d lang=0x%03X : %d 条" % (k[0], k[1], k[2], v))

has_mac = any(r.platformID == 1 for r in nm.names)
print("  有 Mac(platformID=1) 记录: %s" % has_mac)

print()
print("=== SHS 对照 ===")
g = TTFont(SHS, lazy=True)
c2 = Counter((r.platformID, r.platEncID, r.langID) for r in g['name'].names)
for k, v in sorted(c2.items()):
    print("  platform=%d enc=%d lang=0x%03X : %d 条" % (k[0], k[1], k[2], v))
g.close()

print()
print("=== FAIL: fvar/STAT 一致性 ===")
if "fvar" in f:
    fv = f['fvar']
    print("  fvar axes: %s" % [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in fv.axes])
    if fv.instances:
        print("  fvar instances: %d 个" % len(fv.instances))
        for inst in fv.instances[:12]:
            coords = dict(zip([a.axisTag for a in fv.axes], inst.coordinates))
            nm_str = f["name"].getDebugName(inst.subfamilyNameID)
            print("    %-12s %s" % (nm_str, coords))
    else:
        print("  fvar instances: 无"  )
else:
    print("  无 fvar 表")

print()
if "STAT" in f:
    st = f['STAT'].table
    print("  STAT axes: %s" % [(a.AxisTag if hasattr(a,"AxisTag") else a.AxisTag) for a in st.DesignAxisRecord.Axis])
    if st.AxisValueArray:
        print("  STAT AxisValues: %d 个" % len(st.AxisValueArray.AxisValue))
        for av in st.AxisValueArray.AxisValue[:12]:
            tag = av.AxisTag if hasattr(av, 'AxisTag') else '?'
            print("    %s value=%s linked=%s" % (tag, getattr(av, "Value", "?"), getattr(av, "ValueNameID", "?")))
else:
    print("  无 STAT")

print()
print("=== WARN: soft_hyphen (U+00AD) ===")
cm = f.getBestCmap(); h = f['hmtx']
if 0x00AD in cm:
    gn = cm[0x00AD]
    print("  U+00AD %-16s adv=%d" % (gn, h[gn][0]))
else:
    print("  无 U+00AD")

print()
print("=== WARN: mandatory_avar_table ===")
print("  有 avar: %s" % ("avar" in f))

print("=== WARN: ligature_carets ===")
if "GSUB" in f:
    feats = set()
    gs = f['GSUB'].table
    if gs.FeatureList:
        for fr in gs.FeatureList.FeatureRecord:
            feats.add(fr.FeatureTag)
    lig = [x for x in feats if x in ('liga','dlig','clig','rlig','hlig')]
    print("  ligature 特性: %s" % lig)
    print("  有 GDEF LigCaretList: %s" % (f["GDEF"].table.LigCaretList is not None))
f.close()