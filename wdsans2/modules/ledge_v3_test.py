#!/usr/bin/env python3
"""ledge_v3_test - 验证「横笔右侧有阻挡则跳过」判据"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
TARGET = 90.0
MIN_RATIO = 2.8
MAX_H = 200.0


def endp(s):
    if s[0]=='QM': return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def bbox_of(c):
    P = np.array([[c["start"][0],c["start"][1]]] + [[endp(s)[0],endp(s)[1]] for s in c["segs"]], float)
    return P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()


def analyze(C):
    gx0 = min(bbox_of(c)[0] for c in C)
    gx1 = max(bbox_of(c)[1] for c in C)
    gy1 = max(bbox_of(c)[3] for c in C)
    best = None
    for ci, c in enumerate(C):
        segs = c['segs']
        if not all(s[0]=="L" for s in segs): continue
        if len(segs) not in (3,4): continue
        x0,x1,y0,y1 = bbox_of(c)
        w = x1-x0; h = max(y1-y0,1)
        if w < 300 or w/h < MIN_RATIO or h > MAX_H: continue
        if y1 < gy1 - 150: continue
        if best is None or y1 > best[0]:
            best = (y1, ci, x0, x1, y0, y1)
    if not best:
        return None
    y1, ci, bx0, bx1, by0, by1 = best
    gap = gx1 - bx1
    if gap <= TARGET + 0.5:
        return ("no_change", gap, 0)
    # 检查横笔 y 带内、横笔右侧有无其他轮廓
    obstacle = None
    for j, c in enumerate(C):
        if j == ci: continue
        ox0, ox1, oy0, oy1 = bbox_of(c)
        if oy1 < by0 or oy0 > by1: continue   # y 不重叠
        if ox0 <= bx1: continue               # 不在右方
        if obstacle is None or ox0 < obstacle:
            obstacle = ox0
    return ("ok", gap, obstacle)


f = TTFont(R15, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
CH = list("到各冬条备务会俞拿璞理腮膨礅覴璥璈")
print('%-4s %-10s %-10s %s' % ('字','状态','右余','阻挡轮廓左界'))
for ch in CH:
    cp = ord(ch)
    if cp not in cm: continue
    rp = RecordingPen(); gs[cm[cp]].draw(rp)
    C = contours_from_pen(rp.value)
    r = analyze(C)
    if not r:
        print("%-4s (无顶部横笔)" % ch); continue
    print("%-4s %-10s %-10.0f %s" % (ch, r[0], r[1], r[2] if r[2] else "-"))
f.close()