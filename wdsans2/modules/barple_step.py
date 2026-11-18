#!/usr/bin/env python3
# barple_step - verify: did barple turn a slanted edge into a vertical+step?
#
# SHS 及 w900: right edge is one smooth SLANT from (900,~560) down-left.
# Ours: barple aligned the small bar to x=895, creating a VERTICAL segment
# followed by a step at y~546.
#
# Test: measure the right-edge slant in the band y=[460,600] at 900wt.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

T6  = '/workspace/wdsans2/build/masters_T6/master-Heavy-900.otf'
MOD = '/workspace/wdsans2/build/masters_MOD/master-Heavy-900.otf'
R31 = '/workspace/wdsans2/build/masters_R31/master-Heavy-900.otf'
SHS = '/workspace/wdsans/ref/shs/shs-900.otf'


def boxes(path, ch):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
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
        P = np.array(pts)
        out.append((round(P[:,0].min()), round(P[:,0].max()), round(P[:,1].min()), round(P[:,1].max()), len(c["segs"])))
    return out


for lbl, p in [("SHS", SHS), ("T6", T6), ("MOD", MOD), ("R31", R31)]:
    print("%-5s 及 900wt: %s" % (lbl, boxes(p, "及")))