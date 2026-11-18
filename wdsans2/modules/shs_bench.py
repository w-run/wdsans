#!/usr/bin/env python3
# shs_bench - 在 SHS 上找左偏旁 (可能是单轮廓) 作为基准
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

def leftbox(path, ch):
    """SHS: 左偏旁 = 最左侧且尺寸合理的轮廓(组)"""
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    ps=[allpts(c) for c in C]
    gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
    gw=gx1-gx0
    if gw<=0: return None
    cands=[]
    for i,p in enumerate(ps):
        x0,x1=p[:,0].min(),p[:,0].max(); y0,y1=p[:,1].min(),p[:,1].max()
        w=x1-x0; h=y1-y0
        if w<100 or h<100: continue
        if not (0.25 < w/h < 2.5): continue
        if x0 > gx0+gw*0.25: continue   # 必须很靠左
        cands.append((x0,i,x0,x1,y0,y1,len(C[i]["segs"])))
    if not cands: return None
    cands.sort()
    _,i,x0,x1,y0,y1,ns = cands[0]
    return x0,x1,y0,y1,(y0+y1)/2,ns

SHS="/workspace/wdsans/ref/shs/shs-400.otf"
OPS="/workspace/wdsans/ref/ops/ops-400.ttf"
CH="叫叨叩叶叽叼叭叮叱昨晴暗晚旺昧昭昕晌晖明"
print("%-2s | %-32s | %-32s" % ("ch","SHS 左偏旁","OPPO 左偏旁"))
print("-"*72)
for ch in CH:
    a=leftbox(SHS,ch); b=leftbox(OPS,ch)
    fa="x[%3.0f,%3.0f] y[%4.0f,%4.0f] c%3.0f n%d" % (a[0],a[1],a[2],a[3],a[4],a[5]) if a else "  ---"
    fb="x[%3.0f,%3.0f] y[%4.0f,%4.0f] c%3.0f n%d" % (b[0],b[1],b[2],b[3],b[4],b[5]) if b else "  ---"
    print("%-2s | %-32s | %-32s" % (ch, fa, fb))