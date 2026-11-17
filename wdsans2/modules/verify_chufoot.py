#!/usr/bin/env python3
"""verify_chufoot - 验证 chufoot 效果"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R27 = '/workspace/wdsans2/build/masters_R27/'
R28 = '/workspace/wdsans2/build/masters_R28/'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}


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


def bottom(path, tag, ch):
    f = TTFont(path + FN[tag], lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    gy0 = min(allpts(c)[:,1].min() for c in C)
    xs = []
    for c in C:
        for q in allpts(c):
            if q[1] < gy0 + 5:
                xs.append(q[0])
    return (gy0, min(xs), max(xs))


def fmt(x):
    if not x:
        return "-"
    return "y=%.0f x[%.0f,%.0f] kuan=%.0f" % (x[0], x[1], x[2], x[2]-x[1])


for tag in ["250", "400", "900"]:
    a = bottom(R27, tag, "出")
    b = bottom(R28, tag, "出")
    print("%-6s R27: %-32s R28: %s" % (tag, fmt(a), fmt(b)))