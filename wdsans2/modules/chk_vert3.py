#!/usr/bin/env python3
"""直接看改后槽位的轮廓签名 + 每段明细"""
import sys, json
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

NEW="/workspace/wdsans2/build/tv2_all.otf"
MAP=json.load(open("/workspace/wdsans2/build/tv2_map.json"))

f=TTFont(NEW,lazy=True); gs=f.getGlyphSet()
for ch,g in MAP.items():
    rp=RecordingPen()
    try:
        gs[g].draw(rp)
    except Exception as e:
        print("  %s ERR %s"%(ch,e)); continue
    C=contours_from_pen(rp.value)
    print("=== %s (%s) ===" % (ch,g))
    for ci,c in enumerate(C):
        segs=c["segs"]
        st=[c["start"]]
        for s in segs[:-1]:
            if s[0]=="L": st.append(s[1])
            elif s[0]=="C": st.append(s[3])
            elif s[0]=="Q": st.append(s[2])
            elif s[0]=="QM": st.append(s[1][-1])
        sig="".join(s[0] for s in segs)
        pts=[tuple(c["start"])]
        for s in segs:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts.append(tuple(s[3]))
            elif s[0]=="Q": pts.append(tuple(s[2]))
            elif s[0]=="QM": pts.append(tuple(s[1][-1]))
        xs=[p[0] for p in pts]
        print("  轮廓%d %s  xmax=%.0f" % (ci,sig,max(xs)))
        if max(xs) > 700:
            for j,s in enumerate(segs):
                e=np.array(s[-1],dtype=float); p0=np.array(st[j],dtype=float)
                v=e-p0; L=float(np.linalg.norm(v))
                print("     [%d] %s L=%.0f dx=%.0f dy=%.0f" % (j,s[0],L,v[0],v[1]))
    print()
f.close()
