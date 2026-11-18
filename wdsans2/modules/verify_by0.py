#!/usr/bin/env python3
# verify_by0 - confirm body endpoint y mismatch is the anomaly cause
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R = "/workspace/wdsans2/build/masters_R31/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

print("多 三档: 横笔下缘 vs body 末点 y")
for tag in ["250","400","900"]:
    f=TTFont(R+FN[tag],lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    for c in C:
        b=bb(c); sig="".join(s[0] for s in c["segs"])
        if sig=="LLL" and b[3]>600:
            bar_bot=b[2]; bar_right=b[1]
        if sig=="LCCC" and b[3]>600 and b[1]>700:
            end=np.array(c["segs"][-1][-1],float)
            body_end=(end[0],end[1])
    print("  %s: bar_bot=%.0f bar_right=%.0f  body_end=(%.0f,%.0f)  dy=%+.0f  dx=%+.0f" % (
        tag, bar_bot, bar_right, body_end[0], body_end[1],
        body_end[1]-bar_bot, body_end[0]-bar_right))