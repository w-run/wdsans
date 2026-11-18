#!/usr/bin/env python3
# repro_shortl - test if m_shortl splits 永 into more contours
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_shortl, m_zerocont

SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
SW = 77.0


def ncont(C):
    return len(C)


def summary(C, lbl):
    gt = []
    for c in C:
        st = np.array(c["start"], float)
        if c["segs"][0][0] == "QM":
            last = np.array(c["segs"][-1][1][-1], float)
        else:
            last = np.array(c["segs"][-1][-1], float)
        gt.append(round(float(np.hypot(*(last-st))), 1))
    print("  %-14s %d contours  gaps=%s" % (lbl, len(C), gt))


f = TTFont(SHS, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
C0 = contours_from_pen(rp.value)
summary(C0, "SHS raw")

ops = m_shortl.find(C0, SW)
print("  shortl ops:", len(ops))
C1 = m_shortl.apply(C0, ops) if ops else C0
summary(C1, "after shortl")

ops2 = m_zerocont.find(C1)
print("  zerocont ops:", len(ops2))
C2 = m_zerocont.apply(C1, ops2) if ops2 else C1
summary(C2, "after zerocont")