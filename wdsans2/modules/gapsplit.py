#!/usr/bin/env python3
# gapsplit - 用轮廓 x 分布的最大间隙切左右部件
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

def split_lr(C):
    """返回 (left_ids, right_ids, gap_x) 或 None"""
    ps=[allpts(c) for c in C]
    if len(ps)<2: return None
    ivs=sorted([(p[:,0].min(), p[:,0].max(), i) for i,p in enumerate(ps)])
    gx0=min(x0 for x0,_,_ in ivs); gx1=max(x1 for _,x1,_ in ivs)
    gw=gx1-gx0
    if gw<=0: return None
    # 在 30%~60% 范围内找最大的「无轮廓覆盖」区间
    best=(0, None)
    lo=gx0+gw*0.28; hi=gx0+gw*0.62
    step=max(1.0, gw/400)
    x=lo
    while x < hi:
        # 该 x 是否被任何轮廓覆盖
        cov = any(a <= x <= b for a,b,_ in ivs)
        if not cov:
            # 向后找连续无覆盖区
            st=x; x2=x
            while x2 < hi and not any(a <= x2 <= b for a,b,_ in ivs):
                x2 += step
            if x2-st > best[0]:
                best=(x2-st, (st+x2)/2)
            x = x2
        else:
            x += step
    if best[1] is None:
        return None
    cut = best[1]
    left=[i for i,p in enumerate(ps) if p[:,0].max() <= cut+2]
    right=[i for i,p in enumerate(ps) if p[:,0].min() >= cut-2]
    return left, right, best[0]

for lbl,p,chars in [
  ("R32","/workspace/wdsans2/build/masters_R32/master-Regular-400.otf","叫叨叩叶叹叽叮叱昨晴暗晚"),
  ("SHS","/workspace/wdsans/ref/shs/shs-400.otf","叫叨叩叶叹叽叮叱昨晴暗晚")]:
    f=TTFont(p,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    print("=== %s ===" % lbl)
    for ch in chars:
        if ord(ch) not in cm: continue
        rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C=contours_from_pen(rp.value)
        r=split_lr(C)
        if not r:
            print("  %s  无间隙" % ch); continue
        L,R,gap=r
        ps=[allpts(c) for c in C]
        if not L: print("  %s  left空 gap=%.0f"%(ch,gap)); continue
        ly0=min(ps[i][:,1].min() for i in L); ly1=max(ps[i][:,1].max() for i in L)
        lx0=min(ps[i][:,0].min() for i in L); lx1=max(ps[i][:,0].max() for i in L)
        ry0=min(ps[i][:,1].min() for i in R) if R else 0
        ry1=max(ps[i][:,1].max() for i in R) if R else 0
        print("  %s L=%d R=%d gap=%.0f | 左 y[%4.0f,%4.0f] 高%3.0f x[%3.0f,%3.0f] | 右 y[%4.0f,%4.0f]" % (
            ch, len(L), len(R), gap, ly0,ly1,ly1-ly0, lx0,lx1, ry0,ry1))
    f.close(); print()