#!/usr/bin/env python3
# ji_corner - dump 及 contour structure at all three weights
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
FS = [('250','master-ExtraLight-250.otf'), ('400','master-Regular-400.otf'), ('900','master-Heavy-900.otf')]


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


for tag, fn in FS:
    f = TTFont(B + fn, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("及")]].draw(rp); f.close()
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
        sig = "".join(s[0] for s in c["segs"])
        print("  c%d %-12s x[%4.0f,%4.0f] y[%4.0f,%4.0f]  %d段" % (
            ci, sig, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), len(c["segs"])))
        # 打印右侧（x > 700）的轮廓点序列
        if P[:,0].max() > 700 and len(c["segs"]) >= 4:
            print("      起点 (%.1f, %.1f)" % (c["start"][0], c["start"][1]))
            for k, s in enumerate(c["segs"]):
                e = s[-1]
                extra = ""
                if s[0] == "C": extra = " c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
                elif s[0] == "Q": extra = " c(%.0f,%.0f)" % (s[1][0],s[1][1])
                print("        %2d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], extra))
    print()