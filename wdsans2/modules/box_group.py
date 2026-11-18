#!/usr/bin/env python3
# box_group - 把拆散的笔画按「封闭方框」聚合回一个部件
#
# 我们的「口」旁 = 4 条独立笔画 (上下横 + 左右竖)
# 聚合方法: 找 x/y 范围互相贴近的多条笔画, 它们的并集构成一个矩形方框
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

def find_box_group(C):
    """在左侧找 4 条笔画, 其并集构成封闭方框"""
    ps=[allpts(c) for c in C]
    gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
    gw=gx1-gx0
    # 左侧候选: 右缘在左 50% 内
    cand=[i for i,p in enumerate(ps) if p[:,0].max() < gx0+gw*0.50]
    if len(cand) < 3: return None
    # 取并集, 找能组成矩形的子集: 用 x/y 范围聚合
    best=None
    n=len(cand)
    import itertools
    for r in range(3, min(n,7)+1):
        for comb in itertools.combinations(cand, r):
            P=np.vstack([ps[i] for i in comb])
            x0,x1=P[:,0].min(),P[:,0].max(); y0,y1=P[:,1].min(),P[:,1].max()
            w=x1-x0; h=y1-y0
            if w<150 or h<150: continue
            if not (0.5 < w/h < 2.0): continue
            # 覆盖率: 这些笔画必须填满矩形边框 (检查四条边附近有墨)
            cov = 0
            for (cx0,cx1,cy0,cy1) in [(x0,x1,y0,y0+40),(x0,x1,y1-40,y1),(x0,x0+40,y0,y1),(x1-40,x1,y0,y1)]:
                sel=[p for p in [ps[i] for i in comb] if p[:,0].max()>=cx0 and p[:,0].min()<=cx1 and p[:,1].max()>=cy0 and p[:,1].min()<=cy1]
                if sel: cov += 1
            if cov < 4: continue
            score = w*h
            if best is None or score > best[0]:
                best=(score, comb, x0,x1,y0,y1)
    return best

R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
f=TTFont(R,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
print("口旁字: 聚合出的方框")
for ch in "叫叨叩叶叹叽叼叭叮叱":
    if ord(ch) not in cm: continue
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp)
    C=contours_from_pen(rp.value)
    b=find_box_group(C)
    if b:
        _,comb,x0,x1,y0,y1 = b
        print("  %s  轮廓%s  x[%.0f,%.0f] y[%.0f,%.0f]  宽%.0f高%.0f 中心%.0f" % (
            ch, list(comb), x0,x1,y0,y1, x1-x0, y1-y0, (y0+y1)/2))
    else:
        print("  %s  未找到" % ch)
f.close()