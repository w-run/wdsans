#!/usr/bin/env python3
# trace_ji - trace 及 c2/c3 right edges through all build stages
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',   B+'masters_T6/master-Regular-400.otf'),
  ('MOD',  B+'masters_MOD/master-Regular-400.otf'),
  ('R1',   B+'masters_R1/master-Regular-400.otf'),
  ('R15',  B+'masters_R15/master-Regular-400.otf'),
  ('R31',  B+'masters_R31/master-Regular-400.otf'),
]


def info(path):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("及")]].draw(rp); f.close()
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
        out.append((len(c["segs"]), P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    return out


print("%-6s %-4s %s" % ("stage", "n", "contours (segs, x0, x1, y0, y1)"))
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    cs = info(p)
    # 找右侧的横笔/竖笔
    hi = [c for c in cs if c[2] > 700]
    desc = " | ".join("c(%d,x%.0f-%.0f,y%.0f-%.0f)" % (n,x0,x1,y0,y1) for n,x0,x1,y0,y1 in hi)
    print("  %-6s %-4d %s" % (lbl, len(cs), desc))