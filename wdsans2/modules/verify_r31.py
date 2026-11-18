#!/usr/bin/env python3
# verify_r31 - confirm seam closure across weights + visual improvement
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B30 = '/workspace/wdsans2/build/masters_R30/'
B31 = '/workspace/wdsans2/build/masters_R31/'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


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


def seams(path, ch):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
    for ci, c in enumerate(C):
        if len(c["segs"]) < 3:
            continue
        st = np.array(c["start"], float)
        gap = float(np.hypot(*(endp(c["segs"][-1]) - st)))
        if not (0.8 < gap < 12):
            continue
        if area(poly(c))/max(gap,1e-6) > 1000:
            out.append((ci, round(gap,1)))
    return out


print('永 seam check:')
for ch in '永':
    for tag in ["250","400","900"]:
        a = seams(B30+FN[tag], ch)
        b = seams(B31+FN[tag], ch)
        print("  %s %s: before=%s after=%s" % (tag, ch, a if a else "none", b if b else "none"))

print()
print('full-library seam count:')
for lbl, base in [("R30", B30), ("R31", B31)]:
    f = TTFont(base + FN["400"], lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    ng = 0; nc = 0
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        k = 0
        for c in C:
            if len(c["segs"]) < 3:
                continue
            st = np.array(c["start"], float)
            gap = float(np.hypot(*(endp(c["segs"][-1]) - st)))
            if not (0.8 < gap < 12):
                continue
            if area(poly(c))/max(gap,1e-6) > 1000:
                k += 1
        if k:
            ng += 1; nc += k
    f.close()
    print("  %s: %d glyphs, %d seams" % (lbl, ng, nc))