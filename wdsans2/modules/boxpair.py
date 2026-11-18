#!/usr/bin/env python3
# boxpair - 找「口/日」类左偏旁 = 左侧若干轮廓的并集, 构成闭合矩形
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

def left_box(C):
    """返回 (轮廓索引列表, x0,x1,y0,y1) 或 None"""
    ps=[allpts(c) for c in C]
    gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
    gw=gx1-gx0
    if gw<=0: return None
    # 左侧轮廓: 右缘 <= 左 50%
    ids=[i for i,p in enumerate(ps) if p[:,0].max() <= gx0+gw*0.50]
    if len(ids)<1: return None
    # 取这些轮廓的并集
    P=np.vstack([ps[i] for i in ids])
    x0,x1=P[:,0].min(),P[:,0].max(); y0,y1=P[:,1].min(),P[:,1].max()
    w=x1-x0; h=y1-y0
    if w<150 or h<150: return None
    if not (0.5 < w/h < 2.2): return None
    return ids, x0,x1,y0,y1

for lbl,p,chars in [("R32","/workspace/wdsans2/build/masters_R32/master-Regular-400.otf","叫叨叩叶叹叽叼叭叮叱"),
                    ("SHS","/workspace/wdsans/ref/shs/shs-400.otf","叫叨叩叶叹叽叼叭叮叱")]:
    f=TTFont(p,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    print("=== %s ===" % lbl)
    for ch in chars:
        if ord(ch) not in cm: continue
        rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C=contours_from_pen(rp.value)
        r=left_box(C)
        if r:
            ids,x0,x1,y0,y1=r
            print("  %s ids=%s x[%.0f,%.0f] y[%.0f,%.0f] 宽%.0f高%.0f 中心%.0f" % (
                ch, ids, x0,x1,y0,y1, x1-x0, y1-y0, (y0+y1)/2))
        else:
            print("  %s None" % ch)
    f.close()
    print()