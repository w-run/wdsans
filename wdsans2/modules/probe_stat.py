#!/usr/bin/env python3
"""probe_stat - 深入分析 fvar/STAT 不一致"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
fv = f["fvar"]
axis_tags = [a.axisTag for a in fv.axes]
print("=== fvar ===")
print("  axes: %s" % [(a.axisTag, a.minValue, a.defaultValue, a.maxValue) for a in fv.axes])
print("  instances: %d" % len(fv.instances))
for i, inst in enumerate(fv.instances):
    coords = inst.coordinates
    nm = f["name"].getDebugName(inst.subfamilyNameID)
    print("    [%d] %-12s coords=%s nameID=%d" % (i, nm, coords, inst.subfamilyNameID))

print()
print("=== STAT 详细 ===")
st = f["STAT"].table
print("  ElidedFallbackNameID: %s" % getattr(st, "ElidedFallbackNameID", "无"))
axes_r = st.DesignAxisRecord.Axis
print("  DesignAxisRecord: %d 个" % len(axes_r))
for a in axes_r:
    print("    tag=%s nameID=%d order=%d" % (a.AxisTag, a.AxisNameID, a.AxisOrdering))

if st.AxisValueArray:
    avs = st.AxisValueArray.AxisValue
    print("  AxisValueArray: %d 个" % len(avs))
    for av in avs:
        fmt = av.Format
        tag = getattr(av, 'AxisTag', None)
        val = getattr(av, 'Value', None)
        nid = getattr(av, 'ValueNameID', None)
        nm = f['name'].getDebugName(nid) if nid else '?'
        print("    fmt=%d tag=%s value=%s nameID=%s (%s)" % (fmt, tag, val, nid, nm))
else:
    print("  AxisValueArray: 无")

print()
print("=== 问题定位 ===")
n_inst = len(fv.instances)
n_av = len(st.AxisValueArray.AxisValue) if st.AxisValueArray else 0
print("  fvar instance 数: %d" % n_inst)
print("  STAT AxisValue 数: %d" % n_av)
print('  fontbakery 要求: 每个 fvar instance 的 wght 值都应在 STAT 有对应 AxisValue')

# 检查 STAT 里有哪些 wght 值
stat_vals = set()
if st.AxisValueArray:
    for av in st.AxisValueArray.AxisValue:
        v = getattr(av, 'Value', None)
        if v is not None:
            stat_vals.add(round(float(v), 1))
print("  STAT 已定义的值: %s" % sorted(stat_vals))
missing = []
for inst in fv.instances:
    w = inst.coordinates.get('wght')
    if w is not None and round(float(w), 1) not in stat_vals:
        missing.append((f['name'].getDebugName(inst.subfamilyNameID), w))
print("  缺失的 instance: %s" % missing)
f.close()