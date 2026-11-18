#!/usr/bin/env python3
# find_exceptions - the 2 barple ops where the bar tip is NOT inside
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
SW = 77.0


def pip(pt, P):
    x, y = pt; inside = False; n = len(P)
    for i in range(n):
        x1, y1 = P[i]; x2, y2 = P[(i+1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2-x1)*(y-y1)/(y2-y1) + x1
            if x < xin: inside = not inside
    return inside


f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    try:
        hits = m_barple.find(C, SW)
    except Exception:
        continue
    for bi, ci, ei, xL, xR, by0 in hits:
        bb = m_barple.bbox(C[bi])
        ymid = (bb[2]+bb[3])/2.0
        P = m_barple.poly(C[ci], 200)
        if not pip((bb[1], ymid), P):
            print("  %s  bar.x1=%.0f ymid=%.0f xR=%.0f by0=%.0f ei=%d" % (
                chr(cp), bb[1], ymid, xR, by0, ei))
f.close()
print("done")