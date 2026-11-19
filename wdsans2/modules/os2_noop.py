#!/usr/bin/env python3
"""os2_noop - 测试 OS/2 v3->v4 不改变其他字段"""
import os, shutil
from fontTools.ttLib import TTFont

SRC = "/workspace/wdsans2/build/masters_R35/master-Regular-400.otf"
OUT = "/tmp/os2v4_test.otf"

f = TTFont(SRC)
o = f["OS/2"]
print("=== 改前 ===")
print("  version=%d" % o.version)

# 记录所有字段
FIELDS = [a for a in dir(o) if not a.startswith('_') and not callable(getattr(o, a))]
before = {}
for a in FIELDS:
    try:
        before[a] = getattr(o, a)
    except Exception:
        pass
print("  记录 %d 个字段" % len(before))

# 升级到 v4
o.version = 4
if not hasattr(o, 'usLowerOpticalPointSize'):
    o.usLowerOpticalPointSize = 0
if not hasattr(o, 'usUpperOpticalPointSize'):
    o.usUpperOpticalPointSize = 0xFFFF

f["post"].formatType = 3.0
f["post"].glyphOrder = None
f.save(OUT)
f.close()

print()
print("=== 读回对比 ===")
g = TTFont(OUT, lazy=True)
o2 = g["OS/2"]
print("  version=%d" % o2.version)
diff = []
for a, v in before.items():
    try:
        v2 = getattr(o2, a)
    except Exception:
        continue
    if v != v2 and not isinstance(v, (list, dict)):
        diff.append((a, v, v2))
if diff:
    print("  字段变化:")
    for a, v, v2 in diff:
        print("    %-24s %s -> %s" % (a, v, v2))
else:
    print("  字段无变化 ✓")

print()
print("  字形数=%d cmap=%d" % (g["maxp"].numGlyphs, len(g.getBestCmap())))
print("  文件大小: %d -> %d" % (os.path.getsize(SRC), os.path.getsize(OUT)))
g.close()