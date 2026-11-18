#!/usr/bin/env python3
# scope2 - m_barple2 全库命中统计 (只检测, 不改)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple2, m_barple

B = "/workspace/wdsans2/build/masters_T6/"
f = TTFont(B + "master-Regular-400.otf", lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
n2 = 0; chars2 = []
n1 = 0
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    try:
        C = contours_from_pen(rp.value)
        h2 = m_barple2.find(C)
        h1 = m_barple.find(C, 77.0)
    except Exception:
        continue
    if h1: n1 += 1
    if h2:
        n2 += 1
        if len(chars2) < 40: chars2.append(chr(cp))
f.close()
print("m_barple  命中: %d 字" % n1)
print("m_barple2 命中: %d 字" % n2)
print("  样例: " + "".join(chars2))