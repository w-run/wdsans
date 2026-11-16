#!/usr/bin/env python3
"""gap_zoom - 把发现缝隙的两个轮廓局部放大, 确认是真缝还是相接"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
NFLAT = 16


def cpts(rp):
    out=[];cur=[];last=None
    for op,args in rp:
        if op=='moveTo':
            if cur: out.append(np.array(cur))
            cur=[np.array(args[0],float)]; last=cur[0]
        elif op=='lineTo':
            p=np.array(args[0],float); cur.append(p); last=p
        elif op=='curveTo':
            P=[last,np.array(args[0],float),np.array(args[1],float),np.array(args[2],float)]
            for i in range(1,NFLAT+1):
                try: cur.append(bezierTools.splitCubicAtT(*P,i/NFLAT)[0][-1])
                except Exception: pass
            last=P[3]
        elif op=='closePath':
            if len(cur)>1: out.append(np.array(cur))
            cur=[]; last=None
    if len(cur)>1: out.append(np.array(cur))
    return [c for c in out if len(c)>=3]


def pairs(ch, i, j):
    f=TTFont(OURS,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    cs=cpts(rp.value)
    a=cs[i]; b=cs[j]
    d2=((a[:,None,:]-b[None,:,:])**2).sum(axis=2)
    k=np.unravel_index(d2.argmin(), d2.shape)
    pa=a[k[0]]; pb=b[k[1]]
    print('%s: c%d(points=%d) <-> c%d(points=%d)'%(ch,i,len(a),j,len(b)))
    print('  最近点 A(%.1f,%.1f)  B(%.1f,%.1f)  距离 %.2f'%(pa[0],pa[1],pb[0],pb[1],np.sqrt(d2[k])))
    # 该点附近两个轮廓各自的点范围
    for nm,c,q in (('A',a,k[0]),('B',b,k[1])):
        lo=max(0,q-6); hi=min(len(c),q+7)
        print('  %s 邻域: %s'%(nm, ' '.join('(%.0f,%.0f)'%(p[0],p[1]) for p in c[lo:hi])))
    return np.sqrt(d2[k])


for ch, i, j in [('靡',15,17),('廖',0,12),('签',0,8),('窝',7,8),('熔',9,11),('秩',1,9)]:
    try:
        pairs(ch,i,j)
    except Exception as e:
        print('%s 失败: %s'%(ch,e))
    print('')