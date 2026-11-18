#!/usr/bin/env python3
# alt_foot - 放宽判据: 找任何「竖条底端显著低于方框底」的情况
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def allpts(c):
    import numpy as np
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)

R="/workspace/wdsans2/build/masters_R33/master-Regular-400.otf"
f=TTFont(R,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
print("找「方框+任意竖条底端低于方框20~120」的字:")
found=[]
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    if len(C)<2: continue
    ps=[allpts(c) for c in C]
    gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps); gw=gx1-gx0
    if gw<=0: continue
    for i,c in enumerate(C):
        sig="".join(s[0] for s in c["segs"])
        if sig not in ("LLL","LLLL"): continue
        p=ps[i]; x0,x1=p[:,0].min(),p[:,0].max(); y0,y1=p[:,1].min(),p[:,1].max()
        w=x1-x0; h=y1-y0
        if h<150 or w>h*0.6: continue
        # 只看左侧
        if x0 > gx0+gw*0.55: continue
        for j,c2 in enumerate(C):
            if j==i: continue
            sig2="".join(s[0] for s in c2["segs"])
            if len(sig2)<5: continue
            q=ps[j]; qx0,qx1=q[:,0].min(),q[:,0].max(); qy0,qy1=q[:,1].min(),q[:,1].max()
            qw=qx1-qx0; qh=qy1-qy0
            if qw<100 or qh<100: continue
            if qx1 > gx0+gw*0.60: continue
            # 竖条与方框有 x 交集
            if min(x1,qx1) - max(x0,qx0) < 20: continue
            d = qy0 - y0
            if 20 < d < 120:
                found.append((chr(cp), round(d)))
                break
        else:
            continue
        break
f.close()
print("  命中 %d 字" % len(found))
print("  " + " ".join("%s(%d)"%(c,d) for c,d in found[:60]))