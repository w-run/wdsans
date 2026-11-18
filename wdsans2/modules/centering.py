#!/usr/bin/env python3
# centering - 测左偏旁(口/日/囗/田/目)的垂直居中 vs 右侧主体
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

def analyze(path, lbl, chars):
    f=TTFont(path, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    print("=== %s ===" % lbl)
    print("  ch  leftYrange      lc   rightYrange    rc     lc-rc")
    for ch in chars:
        if ord(ch) not in cm: continue
        rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C=contours_from_pen(rp.value)
        if len(C) < 2: continue
        gx0=min(allpts(c)[:,0].min() for c in C)
        gx1=max(allpts(c)[:,0].max() for c in C)
        mid=gx0+(gx1-gx0)*0.5
        left=[]; right=[]
        for c in C:
            P=allpts(c)
            cx=(P[:,0].min()+P[:,0].max())/2
            if cx < mid: left.append(P)
            else: right.append(P)
        if not left or not right: continue
        ly0=min(p[:,1].min() for p in left);  ly1=max(p[:,1].max() for p in left)
        ry0=min(p[:,1].min() for p in right); ry1=max(p[:,1].max() for p in right)
        lc=(ly0+ly1)/2; rc=(ry0+ry1)/2
        print("  %s  [%5.0f,%5.0f] %5.0f   [%5.0f,%5.0f] %5.0f  %+6.0f" % (
            ch, ly0,ly1,lc, ry0,ry1,rc, lc-rc))
    f.close()
    print()

R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
S="/workspace/wdsans/ref/shs/shs-400.otf"
O="/workspace/wdsans/ref/ops/ops-400.ttf"
CH = "明昨晴暗晚旺昧昭昕晌晖"
analyze(R, "R32 (ours)", CH)
analyze(S, "SHS", CH)
analyze(O, "OPPO", CH)