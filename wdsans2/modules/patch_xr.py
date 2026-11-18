#!/usr/bin/env python3
# patch_xr - 验证: 在现有 master 上把 bar 右端移到本档 xR, 撇厚能否回到 SHS 水平
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
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

def poly(c, n=300):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="C":
            p0=pts[-1]; c1=np.array(s[1],float); c2=np.array(s[2],float); p3=np.array(s[3],float)
            for i in range(1,n+1):
                t=i/n; mt=1-t
                pts.append(mt**3*p0+3*mt*mt*t*c1+3*mt*t*t*c2+t**3*p3)
        elif s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        else:
            pts.append(np.array(s[1],float))
    return np.array(pts)

def xcross(P, y):
    xs=[]
    for i in range(len(P)-1):
        a=P[i]; b=P[i+1]
        if (a[1]-y)*(b[1]-y) <= 0 and abs(b[1]-a[1]) > 1e-9:
            t=(y-a[1])/(b[1]-a[1]); xs.append(a[0]+t*(b[0]-a[0]))
    return sorted(xs)

for tag, fn in [("250","master-ExtraLight-250.otf"),("400","master-Regular-400.otf"),("900","master-Heavy-900.otf")]:
    f=TTFont("/workspace/wdsans2/build/masters_R34/"+fn, lazy=True)
    gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    bar=body=None
    for c in C:
        sig="".join(s[0] for s in c["segs"])
        P=allpts(c)
        if sig=="LLL" and P[:,1].max()>600: bar=c
        elif sig=="LCCC" and P[:,1].max()>600 and P[:,0].max()>700: body=c
    if not bar or not body:
        print("%s: bar=%s body=%s" % (tag, bool(bar), bool(body))); continue
    bp=allpts(bar); bar_bot=bp[:,1].min(); bar_right=bp[:,0].max()
    xs=xcross(poly(body), bar_bot)
    xR=xs[-1] if xs else None
    print("%s: bar_right=%.0f bar_bot=%.0f -> 本档 xR=%.0f (差 %+.0f)" % (tag, bar_right, bar_bot, xR or 0, (xR-bar_right) if xR else 0))