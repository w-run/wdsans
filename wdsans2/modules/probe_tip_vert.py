#!/usr/bin/env python3
"""看 大 的端面段前后点的准确坐标，确定垂直段应有的长度"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

for lbl,p in (("我们","/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"),
              ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf")):
    f=TTFont(p,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    rp=RecordingPen(); gs[cm[ord("大")]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    print("=== %s 大 ===" % lbl)
    for ci,c in enumerate(C):
        segs=c["segs"]
        pts=[tuple(c["start"])]
        for s in segs:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts.append(tuple(s[3]))
            elif s[0]=="Q": pts.append(tuple(s[2]))
            elif s[0]=="QM": pts.append(tuple(s[1][-1]))
        if max(p[0] for p in pts) < 700: continue
        st=[c["start"]]
        for s in segs[:-1]:
            if s[0]=="L": st.append(s[1])
            elif s[0]=="C": st.append(s[3])
            elif s[0]=="Q": st.append(s[2])
            elif s[0]=="QM": st.append(s[1][-1])
        print("  轮廓%d:" % ci)
        for j,s in enumerate(segs):
            e=s[-1]
            print("    [%d] %-2s  from (%.0f,%.0f) -> (%.0f,%.0f)" % (
                j, s[0], st[j][0], st[j][1], e[0], e[1]))
    print()
