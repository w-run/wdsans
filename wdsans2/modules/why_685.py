#!/usr/bin/env python3
# why_685 - 为什么 m_barple 把 seg3 终点放在 (xR, by0)? by0 从哪来?
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

f=TTFont("/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf", lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
C=contours_from_pen(rp.value)
hits = m_barple.find(C, 30.0)
print("barple.find 返回:", hits)
print()
逐字段解释: (bar_idx, body_idx, ei, xL, xR, by0)
for h in hits:
    bi, ci, ei, xL, xR, by0 = h
    bar=C[bi]; body=C[ci]
    def bb(c):
        P=[np.array(c["start"],float)]
        for s in c["segs"]:
            if s[0]=="QM":
                for q in s[1]: P.append(np.array(q,float))
            elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
            else: P.append(np.array(s[1],float))
        P=np.array(P); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()
    bx0,bx1,byy0,byy1 = bb(bar)
    print("  bar  bbox x[%.0f,%.0f] y[%.0f,%.0f]" % (bx0,bx1,byy0,byy1))
    print("       xR=%.0f (body在y=by0处的右交点)" % xR)
    print("       by0=%.0f (= bar 的下缘 %.0f)" % (by0, byy0))
    print("  body seg%d 终点原为 (%.0f,%.0f)" % (ei, body["segs"][ei][-1][0], body["segs"][ei][-1][1]))
    print("       -> 被改到 (%.0f,%.0f)" % (xR, by0))
    print()