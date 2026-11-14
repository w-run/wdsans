#!/usr/bin/env python3
"""selfx.py - 轮廓自交检测（带 bbox 预筛，避免 O(n^2) 爆炸）

对每个轮廓:
  1. 展平为折线
  2. 对每对非相邻线段, 先用线段 bbox 快速排除
  3. 再做精确相交测试
"""
import sys, json
import numpy as np
sys.path.insert(0,'/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def endp(s):
    if s[0]=='QM': return np.array(s[1][-1],float)
    return np.array(s[-1],float)


def flat(c, steps=32):
    pts=[np.array(c['start'],float)]
    for s in c['segs']:
        if s[0]=='L':
            pts.append(np.array(s[1],float))
        elif s[0]=='C':
            p0=pts[-1]; c1=np.array(s[1],float); c2=np.array(s[2],float); e=np.array(s[3],float)
            for i in range(1,steps+1):
                t=i/steps; mt=1-t
                pts.append(mt**3*p0+3*mt*mt*t*c1+3*mt*t*t*c2+t**3*e)
    return np.array(pts)


def self_intersects(P):
    """P: Nx2 折线（闭合）。返回是否自交"""
    n=len(P)
    if n<6: return False
    # 线段数组
    A=P[:-1]; B=P[1:]
    lo=np.minimum(A,B); hi=np.maximum(A,B)
    for i in range(n-2):
        # 只检查 i+2 之后的（跳过相邻）
        j0=i+2
        j1=n-1
        if i==0: j0=j1-1 if j1-j0>1 else j1
        if j0>=j1: continue
        # bbox 预筛
        mask=(lo[j0:j1,0]<=hi[i,0])&(hi[j0:j1,0]>=lo[i,0])& \
             (lo[j0:j1,1]<=hi[i,1])&(hi[j0:j1,1]>=lo[i,1])
        idxs=np.nonzero(mask)[0]+j0
        if len(idxs)==0: continue
        p1=A[i]; d1=B[i]-A[i]
        for j in idxs:
            p3=A[j]; d2=B[j]-A[j]
            den=d1[0]*d2[1]-d1[1]*d2[0]
            if abs(den)<1e-9: continue
            t=((p3[0]-p1[0])*d2[1]-(p3[1]-p1[1])*d2[0])/den
            u=((p3[0]-p1[0])*d1[1]-(p3[1]-p1[1])*d1[0])/den
            # 收紧: 交点必须离两端都足够远 (排除近似相接)
            if 0.10<t<0.90 and 0.10<u<0.90:
                # 额外: 交叉角不能太小 (排除近乎重合的曲线展平段)
                L1=float(np.linalg.norm(d1)); L2=float(np.linalg.norm(d2))
                if L1<1e-9 or L2<1e-9: continue
                cosang=abs(float(np.dot(d1,d2))/(L1*L2))
                if cosang>0.985: continue
                return True
    return False


def main():
    fp=sys.argv[1] if len(sys.argv)>1 else '/workspace/wdsans2/build/masters_MOD7/master-Regular-400.otf'
    out=sys.argv[2] if len(sys.argv)>2 else '/workspace/wdsans2/build/idx_selfx.json'
    f=TTFont(fp); cm=f.getBestCmap(); gs=f.getGlyphSet()
    cps=[cp for cp in sorted(cm.keys()) if 0x4E00<=cp<=0x9FFF]
    res=[]
    for k,cp in enumerate(cps):
        try:
            rp=RecordingPen(); gs[cm[cp]].draw(rp)
            C=contours_from_pen(rp.value) if rp.value else []
        except Exception: continue
        for ci,c in enumerate(C):
            if self_intersects(flat(c)):
                res.append([cp,ci])
        if (k+1)%3000==0:
            print('  已扫 %d 字, 命中 %d'%(k+1,len(res)), flush=True)
    print('自交: %d 处 (%d 字)'%(len(res),len(set(x[0] for x in res))))
    json.dump({'selfx':res}, open(out,'w'))
    f.close()


main()
