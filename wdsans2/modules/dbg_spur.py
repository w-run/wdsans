#!/usr/bin/env python3
"""dbg_spur - inspect 眼 c4 spur structure precisely"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f = TTFont('/workspace/wdsans2/build/masters_R29/master-Regular-400.otf', lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("眼")]].draw(rp); f.close()
C = contours_from_pen(rp.value)


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


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
    if not (380 < P[:,0].min() < 480 and 640 < P[:,0].max() < 730 and P[:,1].max() < 200):
        continue
    print("c%d  %d segs  x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, len(c["segs"]),
        P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    seq = seqpts(c)
    mx = max(p[0] for p in seq)
    print("  mx=%.1f" % mx)
    print("  start (%.1f,%.1f)" % (c["start"][0], c["start"][1]))
    for k, s in enumerate(c["segs"]):
        e = s[-1]
        tag = " <== x-max" if abs(e[0]-mx) < 3 else ""
        print("   %d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], tag))
        if s[0] == "C" and len(s) >= 4:
            print("        c1(%.1f,%.1f) c2(%.1f,%.1f)" % (s[1][0],s[1][1],s[2][0],s[2][1]))
        if s[0] == "Q" and len(s) >= 3:
            print("        c(%.1f,%.1f)" % (s[1][0],s[1][1]))
    print("  seq:", [(round(p[0]), round(p[1])) for p in seq])