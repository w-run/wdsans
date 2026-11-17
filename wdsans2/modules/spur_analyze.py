#!/usr/bin/env python3
"""spur_analyze - measure the real geometry of the 眼 spur vs SHS"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from canonpen3 import contours_from_pen

SETS = [('R29', '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'),
        ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf')]


for lbl, p in SETS:
    f = TTFont(p, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = DecomposingRecordingPen(gs); gs[cm[ord("眼")]].draw(rp); f.close()
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
        if not (350 < P[:,0].max() < 760 and P[:,1].max() < 250 and P[:,1].min() > -150):
            continue
        # 找该轮廓里「x 最大且 y 局部极高」的点
        seq = [tuple(c["start"])]
        for s in c["segs"]:
            if s[0] == "QM": seq.append(tuple(s[1][-1]))
            elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
            else: seq.append(tuple(s[1]))
        print("  c%d (%d segs) y-range[%.0f,%.0f]" % (ci, len(c["segs"]), P[:,1].min(), P[:,1].max()))
        for k in range(len(seq)):
            p0 = np.array(seq[k]); p1 = np.array(seq[(k+1)%len(seq)])
            # 相邻边的 y 变化
            if p1[1] - p0[1] > 50 and p1[0] > 600:
                print("      seg%d: (%.0f,%.0f)->(%.0f,%.0f)  dy=%.0f" % (
                    k, p0[0],p0[1], p1[0],p1[1], p1[1]-p0[1]))
    print()