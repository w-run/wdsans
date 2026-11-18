#!/usr/bin/env python3
# duo_gap2 - exact notch height at 300 and 350 to confirm the trend
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}


def junction(path, tag):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    bar_y0 = None; slant_end = None
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
        sig = "".join(s[0] for s in c["segs"])
        if sig == "LLL" and P[:,1].max() > 600 and P[:,0].max() > 700:
            bar_y0 = P[:,1].min()
        elif sig == "LCCC" and P[:,0].max() > 700 and P[:,1].max() > 600:
            slant_end = (c["segs"][-1][-1][0], c["segs"][-1][-1][1])
    if bar_y0 is not None and slant_end is not None:
        print("  %-4s bar_bottom_y=%.0f  slant_end=(%.0f,%.0f)  缝=%.0f" % (
            tag, bar_y0, slant_end[0], slant_end[1], bar_y0 - slant_end[1]))


print("R31 多 bar/slant junction:")
for tag in ["250","400","900"]:
    junction(B + FN[tag], tag)

# 也看 T6（拆分后、barple 前）
T6 = '/workspace/wdsans2/build/masters_T6/'
print()
print("T6 (before module chain):")
for tag in ["250","400","900"]:
    junction(T6 + FN[tag], tag)