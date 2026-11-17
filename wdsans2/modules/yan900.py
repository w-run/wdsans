#!/usr/bin/env python3
"""yan900 - 眼 c4 shape at 900wt"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R29/'
for tag, fn in [('400','master-Regular-400.otf'), ('900','master-Heavy-900.otf')]:
    f = TTFont(B + fn, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("眼")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s ===" % tag)
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
        if not (400 < P[:,0].min() < 520 and 620 < P[:,0].max() < 800 and P[:,1].max() < 320 and len(c["segs"]) <= 6):
            continue
        print("  c%d %dsegs x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, len(c["segs"]),
            P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
        print("     start (%.1f,%.1f)" % (c["start"][0], c["start"][1]))
        for k, s in enumerate(c["segs"]):
            e = s[-1]
            extra = ""
            if s[0] == "C": extra = " c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
            elif s[0] == "Q": extra = " c(%.0f,%.0f)" % (s[1][0],s[1][1])
            print("     %d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], extra))
    print()