#!/usr/bin/env python3
# seam_pattern - what is the offset vector distribution?
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:,0]; y = P[:,1]
    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))


f = TTFont("/workspace/wdsans2/build/masters_R30/master-Regular-400.otf", lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
vec = []
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF][:6000]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    for c in C:
        if len(c["segs"]) < 3:
            continue
        st = np.array(c["start"], float); e = endp(c["segs"][-1])
        gap = float(np.hypot(*(e-st)))
        if not (0.8 < gap < 12):
            continue
        if area(poly(c))/max(gap,1e-6) > 1000:
            vec.append(e - st)
f.close()

V = np.array(vec)
print("n =", len(V))
print("dx: min %.2f max %.2f mean %.2f median %.2f" % (V[:,0].min(), V[:,0].max(), V[:,0].mean(), np.median(V[:,0])))
print("dy: min %.2f max %.2f mean %.2f median %.2f" % (V[:,1].min(), V[:,1].max(), V[:,1].mean(), np.median(V[:,1])))
print()
print("rounded offset histogram (top 15):")
from collections import Counter
cnt = Counter((round(v[0]), round(v[1])) for v in V)
for k, n in cnt.most_common(15):
    print("   %s : %d" % (str(k), n))