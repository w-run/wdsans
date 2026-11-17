#!/usr/bin/env python3
"""dbg3w - check 眼 c4 spike at 250/400/900 to calibrate per-weight threshold"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R29/'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


for tag in ["250", "400", "900"]:
    f = TTFont(B + FN[tag], lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("眼")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s: %d contours ===" % (tag, len(C)))
    for ci, c in enumerate(C):
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
        P = np.array(pts)
        if not (380 < P[:,0].min() < 500 and 620 < P[:,0].max() < 780 and P[:,1].max() < 300):
            continue
        seq = seqpts(c)
        mx = max(p[0] for p in seq)
        print("  c%d %dsegs  x[%.0f,%.0f] y[%.0f,%.0f] mx=%.0f" % (ci, len(c["segs"]),
            P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), mx))
        for k, s in enumerate(c["segs"]):
            e = s[-1]
            if abs(e[0] - mx) < 4:
                prev = np.array(seq[k], float)
                rise = e[1] - prev[1]
                ns = c["segs"][(k+1) % len(c["segs"])]
                ty = float(ns[1][1]) if ns[0] in ("C","Q") else float(ns[-1][1])
                print("     tip seg%d -> (%.0f,%.0f)  prev=(%.0f,%.0f)  rise=%.0f  targetY=%.0f" % (
                    k, e[0], e[1], prev[0], prev[1], rise, ty))
    print()