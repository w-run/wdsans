#!/usr/bin/env python3
# ymismatch - 多: bar bottom y vs body slash endpoint y, per weight, T6 and R31
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

T = "/workspace/wdsans2/build/masters_T6/"
R = "/workspace/wdsans2/build/masters_R31/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

def bbox(c):
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
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()

def analyze(path, tag):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("  %s:" % tag)
    for ci, c in enumerate(C):
        b = bbox(c)
        if b[3] < 600:
            continue
        sig = "".join(s[0] for s in c["segs"])
        if sig == "LLL":
            print("     bar  c%d  x[%.0f,%.0f] y[%.0f,%.0f]  y_bot=%.0f" % (ci, b[0],b[1],b[2],b[3], b[2]))
        elif len(c["segs"]) >= 4:
            e = c["segs"][-1][-1]
            print("     body c%d  x[%.0f,%.0f] y[%.0f,%.0f]  last_pt=(%.0f,%.0f)" % (ci, b[0],b[1],b[2],b[3], e[0], e[1]))

print("=== T6 (before barple) ===")
for k in ["250","400","900"]:
    analyze(T + FN[k], k)
print()
print("=== R31 (after barple) ===")
for k in ["250","400","900"]:
    analyze(R + FN[k], k)