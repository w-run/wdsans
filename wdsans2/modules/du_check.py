#!/usr/bin/env python3
# du_check - 都 左下「日」底部右侧出脚 检查
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

def dump(path, lbl, ch):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm:
        print("%s: 无字形" % lbl); f.close(); return
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    print("=== %s %s (%d contours) ===" % (lbl, ch, len(C)))
    for ci,c in enumerate(C):
        b=bb(c); sig="".join(s[0] for s in c["segs"])
        print("  c%-2d %-14s x[%4.0f,%4.0f] y[%4.0f,%4.0f]" % (ci,sig[:14],b[0],b[1],b[2],b[3]))
    print()

R = "/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
S = "/workspace/wdsans/ref/shs/shs-400.otf"
dump(R, "R32", "都")
dump(S, "SHS", "都")