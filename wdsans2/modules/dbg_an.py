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

f=TTFont("/workspace/wdsans2/build/masters_R32/master-Regular-400.otf",lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("暗")]].draw(rp)
C=contours_from_pen(rp.value)
ps=[allpts(c) for c in C]
gx0=min(p[:,0].min() for p in ps); gx1=max(p[:,0].max() for p in ps)
gw=gx1-gx0
print("暗 gx0=%.0f gx1=%.0f gw=%.0f  阈值ux1<=%.0f" % (gx0,gx1,gw,gx0+gw*0.52))
boxes=[(i,p[:,0].min(),p[:,0].max(),p[:,1].min(),p[:,1].max()) for i,p in enumerate(ps)]
TOL=4.0
used=set(); clusters=[]
order=sorted(boxes,key=lambda b:b[1])
for b in order:
    if b[0] in used: continue
    grp=[b]; used.add(b[0])
    for b2 in order:
        if b2[0] in used: continue
        if abs(b2[3]-b[3])<=TOL and abs(b2[4]-b[4])<=TOL:
            grp.append(b2); used.add(b2[0])
    clusters.append(grp)
print()
print("聚类结果:")
for grp in clusters:
    ux0=min(g[1] for g in grp); ux1=max(g[2] for g in grp)
    uy0=min(g[3] for g in grp); uy1=max(g[4] for g in grp)
    w=ux1-ux0; h=uy1-uy0
    ids=[g[0] for g in grp]
    ok1 = "w>=120" if w>=120 else "w<120!"
    ok2 = "h>=120" if h>=120 else "h<120!"
    ok3 = "ratioOK" if (h>0 and 0.45<w/h<2.5) else "ratio!"
    ok4 = "inxOK" if ux1<=gx0+gw*0.52 else "tooRight!"
    print("  ids=%-12s x[%4.0f,%4.0f] y[%4.0f,%4.0f] w%.0f h%.0f  %s %s %s %s" % (
        str(ids), ux0,ux1,uy0,uy1, w,h, ok1,ok2,ok3,ok4))