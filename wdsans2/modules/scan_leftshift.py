#!/usr/bin/env python3
# out - 全库找「左偏旁被额外上移」的字: R32 vs SHS 的左偏旁中心差 >40
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

def centers(path):
    """返回 {cp: (leftC, rightC)} 按 1000 upem 归一"""
    f=TTFont(path, lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out={}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        if len(C)<2: continue
        ps=[allpts(c) for c in C]
        gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
        mid=gx0+(gx1-gx0)*0.5
        l=[]; r=[]
        for p in ps:
            cx=(p[:,0].min()+p[:,0].max())/2
            (l if cx<mid else r).append(p)
        if not l or not r: continue
        ly0=min(p[:,1].min() for p in l); ly1=max(p[:,1].max() for p in l)
        ry0=min(p[:,1].min() for p in r); ry1=max(p[:,1].max() for p in r)
        out[cp]=((ly0+ly1)/2, (ry0+ry1)/2)
    f.close()
    return out

print("loading SHS...", flush=True)
A=centers("/workspace/wdsans/ref/shs/shs-400.otf")
print("loading R32...", flush=True)
B=centers("/workspace/wdsans2/build/masters_R32/master-Regular-400.otf")
print()
bad=[]
for cp in A:
    if cp not in B: continue
    la,ra=A[cp]; lb,rb=B[cp]
    # 左偏旁中心的偏移（相对右主体，消除整体位移）
    da=la-ra; db=lb-rb
    if abs(db-da) > 40:
        bad.append((chr(cp), round(da), round(db), round(db-da)))
bad.sort(key=lambda x: -abs(x[3]))
print("左偏旁相对位置偏移 >40 的字: %d" % len(bad))
for c,da,db,d in bad[:45]:
    print("  %s  SHS相对%+.0f  R32相对%+.0f  差%+.0f" % (c,da,db,d))