#!/usr/bin/env python3
# oppo_profile - rightmost x at each y for OPPO vs ours, 多 400
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def prof(path, lbl, ch, ys):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    segs = []
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            segs.append((prev, s, e)); prev = e
    print("=== %s ===" % lbl)
    for y in ys:
        best = None
        for prev, s, e in segs:
            n = 60 if s[0] != "L" else 2
            for k in range(n+1):
                u = k/n
                if s[0] == "L":
                    q = prev + (e-prev)*u
                elif s[0] == "C":
                    c1 = np.array(s[1],float); c2 = np.array(s[2],float)
                    q = ((1-u)**3)*prev + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*e
                elif s[0] == "Q":
                    c1 = np.array(s[1],float)
                    q = ((1-u)**2)*prev + 2*(1-u)*u*c1 + (u**2)*e
                elif s[0] == "QM":
                    q = None
                    for pq in s[1]:
                        pq = np.array(pq, float)
                        if abs(pq[1]-y) < 3.0:
                            if best is None or pq[0] > best:
                                best = pq[0]
                else:
                    q = None
                if q is not None and abs(q[1]-y) < 3.0:
                    if best is None or q[0] > best:
                        best = q[0]
        print("   y=%4d  x_right=%s" % (y, "%.0f" % best if best else "-"))
    print()


ys = [750, 740, 730, 720, 710, 700, 690, 685]
prof("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO 400", "多", ys)
prof("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", "R31 400", "多", ys)
prof("/workspace/wdsans2/build/masters_T6/master-Regular-400.otf", "T6 400", "多", ys)