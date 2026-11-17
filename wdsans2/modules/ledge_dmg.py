#!/usr/bin/env python3
"""ledge_dmg - 精确测量 m_ledge 对每字的实际改动"""
import sys, json, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R16 = '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'


def endp(s):
    if s[0]=='QM': return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def load(path):
    f = TTFont(path, lazy=True)
    return f, f.getGlyphSet(), f.getBestCmap()


def contour_pts(C):
    out = []
    for c in C:
        P = np.array([[c["start"][0],c["start"][1]]] + [[endp(s)[0],endp(s)[1]] for s in c["segs"]], float)
        out.append(P)
    return out


f15, g15, c15 = load(R15)
f16, g16, c16 = load(R16)

CH = list("乁乾佟候倡偶储兢冀到冬备务各条会俞拿且串丸久之九仇伺伽余做偷偽")
print('%-4s %-10s %-10s %s' % ('字', 'R15 最宽横笔', 'R16 最宽横笔', '右端位移'))
moved = 0
for ch in CH:
    cp = ord(ch)
    if cp not in c15 or cp not in c16:
        continue
    def widest(g, cm):
        rp = RecordingPen(); g[cm[cp]].draw(rp)
        C = contours_from_pen(rp.value)
        best = None
        for P in contour_pts(C):
            x0,x1 = P[:,0].min(), P[:,0].max()
            y0,y1 = P[:,1].min(), P[:,1].max()
            w = x1-x0; h = max(y1-y0,1)
            if w/h < 2.0 or w < 250:
                continue
            if best is None or w > best[0]:
                best = (w, x0, x1, y0, y1)
        return best
    a = widest(g15, c15); b = widest(g16, c16)
    if not a or not b:
        continue
    dx = b[2] - a[2]
    mark = "  <<< 被拉长" if dx > 5 else ""
    if dx > 5: moved += 1
    print("%-4s x[%4.0f,%4.0f]  x[%4.0f,%4.0f]  %+.0f%s" % (ch, a[1], a[2], b[1], b[2], dx, mark))
f15.close(); f16.close()
print()
print('被拉长的字: %d / %d' % (moved, len(CH)))