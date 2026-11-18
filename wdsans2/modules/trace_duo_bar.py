#!/usr/bin/env python3
# trace_duo_bar - trace 多 bar shape through stages at 400wt
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS','/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6', B+'masters_T6/master-Regular-400.otf'),
  ('MOD',B+'masters_MOD/master-Regular-400.otf'),
  ('R1', B+'masters_R1/master-Regular-400.otf'),
  ('R15',B+'masters_R15/master-Regular-400.otf'),
  ('R31',B+'masters_R31/master-Regular-400.otf'),
]


for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    f = TTFont(p, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s (%d contours) ===" % (lbl, len(C)))
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
        if P[:,1].max() > 600 and P[:,0].max() > 700:
            print("   c%d %-18s x[%.0f,%.0f] y[%.0f,%.0f]" % (
                ci, sig[:18], P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    print()