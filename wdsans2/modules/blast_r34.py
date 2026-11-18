#!/usr/bin/env python3
# r34_vs_r32 - R34 相对 R32 的改动爆炸半径检查
#
# 目的: m_boxrad(1040字) + m_radfoot(11字) 是否有意外波及
import sys, os
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

A="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
B="/workspace/wdsans2/build/masters_R34/master-Regular-400.otf"
fa=TTFont(A,lazy=True); fb=TTFont(B,lazy=True)
ga=fa.getGlyphSet(); gb=fb.getGlyphSet(); cm=fa.getBestCmap()
n_changed=0; changed=[]; n_topo=0
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    gn=cm[cp]
    ra=RecordingPen(); rb=RecordingPen()
    try:
        ga[gn].draw(ra); gb[gn].draw(rb)
    except Exception:
        continue
    if ra.value != rb.value:
        n_changed += 1
        Ca=contours_from_pen(ra.value); Cb=contours_from_pen(rb.value)
        sa=["".join(s[0] for s in c["segs"]) for c in Ca]
        sb=["".join(s[0] for s in c["segs"]) for c in Cb]
        if sa != sb:
            n_topo += 1
        if len(changed) < 30: changed.append(chr(cp))
fa.close(); fb.close()
print("R32 -> R34 改动的字: %d" % n_changed)
print("  其中拓扑改变(签名不同): %d  %s" % (n_topo, "OK" if n_topo==0 else "!!!"))
print("  前30字: " + "".join(changed))
print()
print("预期: 1040(boxrad) + 11(radfoot) 可能有重叠 = 约 1040~1051 字")