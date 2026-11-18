#!/usr/bin/env python3
# find_step - locate actual visible steps (overlapping contours w/ right-edge mismatch)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

P = '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf'


def boxes(path):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        bs = []
        for c in C:
            pts = [np.array(c["start"], float)]
            for s in c["segs"]:
                if s[0] == "QM":
                    for q in s[1]: pts.append(np.array(q, float))
                elif s[0] == "C":
                    pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
                elif s[0] == "Q":
                    pts.extend([np.array(s[1],float), np.array(s[2],float)])
                else:
                    pts.append(np.array(s[1], float))
            P2 = np.array(pts)
            bs.append((P2[:,0].min(), P2[:,0].max(), P2[:,1].min(), P2[:,1].max()))
        out[cp] = bs
    f.close()
    return out


print("scanning R31...", flush=True)
A = boxes(P)

res = []
for cp, bs in A.items():
    n = len(bs)
    if n < 2:
        continue
    for i in range(n):
        for j in range(i+1, n):
            a, b = bs[i], bs[j]
            # y 区间必须重叠
            if a[3] <= b[2] or b[3] <= a[2]:
                continue
            # 两者右界都靠字面右（> 70% of max）
            gx = max(x[1] for x in bs)
            if a[1] < gx*0.72 or b[1] < gx*0.72:
                continue
            # 右界差 >= 40 单位 -> 可见台阶
            d = abs(a[1] - b[1])
            if d >= 40:
                res.append((round(d), chr(cp), i, j, round(a[1]), round(b[1])))
                break
        else:
            continue
        break

res.sort(reverse=True)
print()
print("右界错位 >=40 单位的字: %d" % len(res))
print("  " + " ".join("%s(%d)" % (c, d) for d, c, _, _, _, _ in res[:30]))
print()
print("最大 15 个明细:")
for d, c, i, j, x1, x2 in res[:15]:
    print("   %s  差%3d  c%d右=%.0f  c%d右=%.0f" % (c, d, i, x1, j, x2))