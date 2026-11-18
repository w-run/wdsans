#!/usr/bin/env python3
# duo_250 - dump 多 contour structure at 250wt: ours vs SHS
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

OURS = '/workspace/wdsans2/build/masters_R31/master-ExtraLight-250.otf'
SHS  = '/workspace/wdsans/ref/shs/shs-250.otf'


def dump(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s: %d contours ===" % (lbl, len(C)))
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
        print("  c%d %-14s x[%4.0f,%4.0f] y[%4.0f,%4.0f] %d段" % (
            ci, sig, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), len(c["segs"])))
        # 右侧轮廓（x max > 700）打印段序列
        if P[:,0].max() > 700 and len(c["segs"]) <= 8:
            print("      起点 (%.1f,%.1f)" % (c["start"][0], c["start"][1]))
            for k, s in enumerate(c["segs"]):
                e = s[-1]
                ex = ""
                if s[0] == "C": ex = " c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
                elif s[0] == "Q": ex = " c(%.0f,%.0f)" % (s[1][0],s[1][1])
                print("         %d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], ex))
    print()


dump(OURS, "R31 250")
dump(SHS, "SHS 250")