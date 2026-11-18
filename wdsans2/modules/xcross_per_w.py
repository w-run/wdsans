#!/usr/bin/env python3
# xcross_per_w - 各档在"本档 bar_bot" 处求 body 右缘交点
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

def poly(c, n=400):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="C":
            p0=pts[-1]; c1=np.array(s[1],float); c2=np.array(s[2],float); p3=np.array(s[3],float)
            for i in range(1,n+1):
                t=i/n; mt=1-t
                pts.append(mt**3*p0 + 3*mt*mt*t*c1 + 3*mt*t*t*c2 + t**3*p3)
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
            t=(y-a[1])/(b[1]-a[1])
            xs.append(a[0]+t*(b[0]-a[0]))
    return sorted(xs)

print("多 各档: bar 位置 与 本档bar_bot处的body右缘交点")
for tag in ["250","400","900"]:
    f = TTFont(B+FN[tag], lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    bar=body=None
    for c in C:
        b=bb(c); sig="".join(s[0] for s in c["segs"])
        if b[3]<600: continue
        if sig=="LLL": bar=c
        elif sig=="LCCCL": body=c
    bbb=bb(bar)
    P=poly(body)
    xs=xcross(P, bbb[2])
    print("  %s: bar x[%.0f,%.0f] y[%.0f,%.0f]  ->  xcross@y=%.0f = %s" % (
        tag, bbb[0],bbb[1],bbb[2],bbb[3], bbb[2], [round(x) for x in xs[-2:]]))