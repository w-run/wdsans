#!/usr/bin/env python3
# inside_test - is the bar right-end INSIDE the body polygon?
#
# If the bar tip is already covered by the body, there is no overhang and
# m_barple has nothing to fix -> it should skip.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
SW = 77.0


def point_in_poly(pt, P):
    x, y = pt
    inside = False
    n = len(P)
    for i in range(n):
        x1, y1 = P[i]
        x2, y2 = P[(i+1) % n]
        if ((y1 > y) != (y2 > y)):
            xin = (x2-x1)*(y-y1)/(y2-y1) + x1
            if x < xin:
                inside = not inside
    return inside


def check(ch):
    f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    hits = m_barple.find(C, SW)
    if not hits:
        print("  %s: no hit" % ch)
        return
    for bi, ci, ei, xL, xR, by0 in hits:
        bar = C[bi]; body = C[ci]
        bb = m_barple.bbox(bar)
        ymid = (bb[2]+bb[3])/2.0
        P = m_barple.poly(body, 300)
        inside = point_in_poly((bb[1], ymid), P)
        inside_lo = point_in_poly((bb[1], bb[2]+2), P)
        inside_hi = point_in_poly((bb[1], bb[3]-2), P)
        print("  %s: bar.x1=%.0f ymid=%.0f  inside(mid)=%s lo=%s hi=%s  xR=%.0f" % (
            ch, bb[1], ymid, inside, inside_lo, inside_hi, xR))


print("bar 右端是否已在 body 内部（True = 无悬空，不该动）:")
for ch in "多及力刀九几乃予勇永了夕":
    check(ch)