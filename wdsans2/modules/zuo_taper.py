#!/usr/bin/env python3
# zuo_taper - 检查 m_taper/m_stepalign 是否移动了「昨」的日旁
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

def leftbox(path):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    rp=RecordingPen(); gs[cm[ord("昨")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    gx0=min(allpts(c)[:,0].min() for c in C)
    gx1=max(allpts(c)[:,0].max() for c in C)
    mid=gx0+(gx1-gx0)*0.5
    best=None
    for c in C:
        P=allpts(c); sig="".join(s[0] for s in c["segs"])
        cx=(P[:,0].min()+P[:,0].max())/2
        if cx>mid: continue
        if len(sig)<5: continue
        w=P[:,0].max()-P[:,0].min(); h=P[:,1].max()-P[:,1].min()
        if w<100 or h<100: continue
        best=(P[:,1].min(),P[:,1].max(),P[:,0].min(),P[:,0].max())
    return best

print("昨 的「日」旁 bbox:")
for lbl,p in [("SHS","/workspace/wdsans/ref/shs/shs-400.otf"),
              ("T6","/workspace/wdsans2/build/masters_T6/master-Regular-400.otf")]:
    b=leftbox(p)
    if b: print("  %-5s y[%4.0f,%4.0f] x[%4.0f,%4.0f]  高%.0f" % (lbl,b[0],b[1],b[2],b[3],b[1]-b[0]))

# 直接重放 taper 看 ops
sys.path.insert(0,"/workspace/wdsans2/modules")
import m_taper, m_stepalign
f=TTFont("/workspace/wdsans/ref/shs/shs-400.otf", lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("昨")]].draw(rp); f.close()
C=contours_from_pen(rp.value)
print()
sw=77.0
for mod in [m_taper, m_stepalign]:
    try:
        ops = mod.find(C, sw)
        print("  %s ops=%d" % (mod.NAME, len(ops)))
    except Exception as e:
        print("  %s ERR %s" % (getattr(mod,"NAME","?"), e))