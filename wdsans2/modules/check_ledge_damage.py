#!/usr/bin/env python3
"""check_ledge_damage - 检查用户报告的字是否被 m_ledge 改动"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R28 = '/workspace/wdsans2/build/masters_R28/master-Regular-400.otf'


def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for p in s[1]: P.append(np.array(p, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def bars(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for ch in "极条目角眼得田由甲申曲电" :
        if ord(ch) not in cm:
            continue
        rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C = contours_from_pen(rp.value)
        gx1 = max(allpts(c)[:,0].max() for c in C)
        bs = []
        for i, c in enumerate(C):
            P = allpts(c)
            x0,x1 = P[:,0].min(), P[:,0].max()
            y0,y1 = P[:,1].min(), P[:,1].max()
            bs.append((i, round(x0), round(x1), round(y0), round(y1), round(gx1-x1)))
        out[ch] = (round(gx1), bs)
    f.close()
    return out


a = bars(R15)
b = bars(R28)

print('%-3s %-8s %-46s %s' % ('字','右界','R15 各轮廓 (x0,x1,y0,y1,右余)','R28 变化'))
for ch in "极条目角眼得田由甲申曲电":
    if ch not in a or ch not in b:
        continue
    changed = []
    for (i,x0,x1,y0,y1,r0), (j,X0,X1,Y0,Y1,r1) in zip(a[ch][1], b[ch][1]):
        if x0 != X0 or x1 != X1:
            changed.append("c%d x[%d,%d]->[%d,%d] 余%d->%d" % (i, x0, x1, X0, X1, r0, r1))
    print("%-3s %-8d %-46s %s" % (ch, a[ch][0],
          " ".join("c%d[%d,%d]" % (i,x0,x1) for i,x0,x1,_,_,_ in a[ch][1])[:45],
          " | ".join(changed) if changed else "(未变)"))