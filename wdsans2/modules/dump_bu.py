#!/usr/bin/env python3
# dump_bu - 部/陪 的轮廓结构
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)

R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
f=TTFont(R, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
for ch in "部陪鄙郭":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    print("=== %s (%d) ===" % (ch, len(C)))
    for ci,c in enumerate(C):
        P=allpts(c); sig="".join(s[0] for s in c["segs"])
        print("  c%-2d %-16s x[%4.0f,%4.0f] y[%4.0f,%4.0f]  宽%.0f 高%.0f" % (
            ci, sig[:16], P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max(),
            P[:,0].max()-P[:,0].min(), P[:,1].max()-P[:,1].min()))
    print()
f.close()