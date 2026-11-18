#!/usr/bin/env python3
# check_D - numeric: D vs B vs SHS right profile for 多
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

CAND = [
  ('250', 'D', '/workspace/wdsans2/build/trial/D_多_250.otf', '/workspace/wdsans2/build/masters_R31/master-ExtraLight-250.otf', '/workspace/wdsans/ref/shs/shs-250.otf'),
  ('400', 'D', '/workspace/wdsans2/build/trial/D_多_400.otf', '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf', '/workspace/wdsans/ref/shs/shs-400.otf'),
]


def prof(path, ys):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    segs = []
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            segs.append((prev, s, e)); prev = e
    out = []
    for y in ys:
        best = None
        for prev, s, e in segs:
            n = 30 if s[0] != "L" else 2
            for k in range(n+1):
                u = k/n
                if s[0] == "L":
                    q = prev + (e-prev)*u
                elif s[0] == "C":
                    c1 = np.array(s[1],float); c2 = np.array(s[2],float)
                    q = ((1-u)**3)*prev + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*e
                else:
                    c1 = np.array(s[1],float)
                    q = ((1-u)**2)*prev + 2*(1-u)*u*c1 + (u**2)*e
                if abs(q[1]-y) < 3.0:
                    if best is None or q[0] > best:
                        best = q[0]
        out.append(best)
    return out


ys = [720, 700, 680, 660, 640]
for tag, mark, dpath, bpath, spath in CAND:
    print("=== %s ===" % tag)
    D = prof(dpath, ys); B = prof(bpath, ys); S = prof(spath, ys)
    print("   y      D_new    B_now    SHS     D-SHS   B-SHS")
    for i, y in enumerate(ys):
        d = D[i]; b = B[i]; s = S[i]
        fd = "%.0f" % d if d else "-"
        fb = "%.0f" % b if b else "-"
        fs = "%.0f" % s if s else "-"
        dd = "%+.0f" % (d-s) if (d and s) else "-"
        db = "%+.0f" % (b-s) if (b and s) else "-"
        print("  %4d  %-8s %-8s %-8s %-7s %s" % (y, fd, fb, fs, dd, db))
    print()