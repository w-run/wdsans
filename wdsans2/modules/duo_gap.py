#!/usr/bin/env python3
# duo_gap - measure the gap between bar c2 and slant c1 at each weight
#
# R31 多: c1 = slant body (LCCC), c2 = separate bar (LLL)
# Both reach x=770. If c2 bottom (y0) is ABOVE c1 top-right, a notch shows.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_T6/'
B2 = '/workspace/wdsans2/build/masters_R31/'
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}


def seg_list(c):
    out = [(c["start"][0], c["start"][1], "M")]
    for s in c["segs"]:
        e = s[-1]
        out.append((e[0], e[1], s[0]))
    return out


def analyze(path, lbl):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    # 找横笔（LLL，宽高比大）和斜笔（LCCC）
    bar = None; slant = None
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
        if sig == "LLL" and P[:,1].max() > 600:
            bar = (ci, c, (P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
        elif sig == "LCCC" and P[:,0].max() > 700 and P[:,1].max() > 600:
            slant = (ci, c, (P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    print("=== %s ===" % lbl)
    if bar:
        ci, c, b = bar
        print("  bar  c%d x[%.0f,%.0f] y[%.0f,%.0f]  h=%.0f" % (ci, b[0],b[1],b[2],b[3], b[3]-b[2]))
        print("       段: " + " ".join("%s(%.0f,%.0f)" % (t,x,y) for x,y,t in seg_list(c)))
    if slant:
        ci, c, b = slant
        print("  slant c%d x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, b[0],b[1],b[2],b[3]))
        print("       段: " + " ".join("%s(%.0f,%.0f)" % (t,x,y) for x,y,t in seg_list(c)))
    if bar and slant:
        bb, sb = bar[2], slant[2]
        print("  >>> bar bottom y=%.0f, slant right-top y=%.0f, 差=%.0f" % (bb[2], sb[3], bb[2]-sb[3]))
    print()


for tag in ["250","400","900"]:
    analyze(B2 + FN[tag], "R31 " + tag)