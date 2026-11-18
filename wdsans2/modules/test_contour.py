#!/usr/bin/env python3
# test_contour - 轮廓级验证 m_boxrad 效果（可靠口径）
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_boxrad

def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)

def leftinfo(path, ch):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    r=m_boxrad.split_lr(C)
    if not r: return None
    left,right=r
    ps=[allpts(c) for c in C]
    ly0=min(ps[i][:,1].min() for i in left); ly1=max(ps[i][:,1].max() for i in left)
    ry0=min(ps[i][:,1].min() for i in right); ry1=max(ps[i][:,1].max() for i in right)
    return ly0, ly1, ly1-ly0, (ly0+ly1)/2, (ry0+ry1)/2, len(left), len(right)

SRC="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
NEW="/workspace/wdsans2/build/boxrad_test/B.otf"
SHS="/workspace/wdsans/ref/shs/shs-400.otf"
CH="叫叩叮叱晴暗昨叶"
print("%-2s | %-28s | %-28s | %-28s" % ("ch","R32","boxrad后","SHS"))
print("-"*94)
for ch in CH:
    a=leftinfo(SRC,ch); b=leftinfo(NEW,ch); c=leftinfo(SHS,ch)
    fmt=lambda t: "y[%4.0f,%4.0f] h%3.0f c%3.0f" % (t[0],t[1],t[2],t[3]) if t else "  (未切分)"
    print("%-2s | %-28s | %-28s | %-28s" % (ch, fmt(a), fmt(b), fmt(c)))