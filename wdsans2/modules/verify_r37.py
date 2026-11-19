#!/usr/bin/env python3
"""verify_r37 - R37 三档一致性验证"""
from fontTools.ttLib import TTFont

MASTERS = [(250, 'ExtraLight'), (400, 'Regular'), (900, 'Heavy')]
print("%-6s %10s %12s %8s %8s" % ("档位", "head.rev", "nameID5", "mark数", "GDEF总"))
print("-" * 50)
sigs = []
for w, tag in MASTERS:
    p = '/workspace/wdsans2/build/masters_R37/master-%s-%d.otf' % (tag, w)
    f = TTFont(p, lazy=True)
    rev = f["head"].fontRevision
    n5 = f["name"].getDebugName(5)
    cd = f["GDEF"].table.GlyphClassDef.classDefs
    nm = sum(1 for v in cd.values() if v == 3)
    print("%-6d %10.3f %12s %8d %8d" % (w, rev, n5, nm, len(cd)))
    sigs.append((round(rev, 3), n5, nm, len(cd)))
    f.close()

print()
print("三档一致: %s" % (len(set(sigs)) == 1))

print()
print("=== 关键字符 mark 分类 ===")
f = TTFont('/workspace/wdsans2/build/masters_R37/master-Regular-400.otf', lazy=True)
cm = f.getBestCmap()
cd = f["GDEF"].table.GlyphClassDef.classDefs
for cp in (0x20DD, 0x20DE, 0x0303, 0x0308, 0x302A, 0x3099):
    if cp not in cm:
        print("  U+%04X 无" % cp)
        continue
    gn = cm[cp]
    cls = cd.get(gn)
    tag = "mark(3)" if cls == 3 else str(cls)
    print("  U+%04X %-16s class=%s" % (cp, gn, tag))
f.close()