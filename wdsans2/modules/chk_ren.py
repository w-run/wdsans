#!/usr/bin/env python3
"""检查 人 为什么没改"""
import sys, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

IDX=json.load(open("/workspace/wdsans2/build/vertend_idx.json"))
f=TTFont("/workspace/wdsans2/build/VF_R41_final.otf",lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
gn=cm[ord("人")]
print("人 glyph =", gn)
print("在索引中:", gn in IDX)
if gn in IDX:
    print("索引记录:", IDX[gn])
rp=RecordingPen(); gs[gn].draw(rp); f.close()
C=contours_from_pen(rp.value)
def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st
for ci,c in enumerate(C):
    segs=c["segs"]
    st=seg_starts(c)
    pts=[tuple(c["start"])]
    for s in segs:
        if s[0]=="L": pts.append(tuple(s[1]))
        elif s[0]=="C": pts.append(tuple(s[3]))
        elif s[0]=="Q": pts.append(tuple(s[2]))
        elif s[0]=="QM": pts.append(tuple(s[1][-1]))
    print("  轮廓%d %s xmax=%.0f" % (ci,"".join(s[0] for s in segs), max(p[0] for p in pts)))
    for j,s in enumerate(segs):
        e=s[-1]; p0=st[j]
        v=np.array(e,dtype=float)-np.array(p0,dtype=float)
        L=float(np.linalg.norm(v))
        print("    [%d] %s L=%.0f dx=%.0f dy=%.0f" % (j,s[0],L,v[0],v[1]))
