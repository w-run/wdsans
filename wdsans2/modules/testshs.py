#!/usr/bin/env python3
# testshs - 用 SHS 的原始横笔长度(722)试一版, 看撇厚度是否回到 28
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

T = "/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf"
OUT = "/workspace/wdsans2/build/plan1b/SHS_250.otf"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

f = TTFont(T)
gs = f.getGlyphSet(); cm = f.getBestCmap()
gn = cm[ord("多")]
rp = RecordingPen(); gs[gn].draw(rp)
C = contours_from_pen(rp.value)

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

for ci,c in enumerate(C):
    b=bb(c); sig="".join(s[0] for s in c["segs"])
    if b[3]>600:
        print("  c%d %-8s x[%.0f,%.0f] y[%.0f,%.0f]" % (ci,sig,b[0],b[1],b[2],b[3]))

# T6 250: bar x 到 745, body seg3->(768,725) seg4->(750,739)
# 试: 完全不做 barple, 直接看效果 (T6 原样)
print()
print("T6 原样即 barple 前状态")