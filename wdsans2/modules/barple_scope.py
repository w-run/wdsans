#!/usr/bin/env python3
# barple_scope - how many glyphs does barple touch where the bar ends up
# sticking out past a slanted neighbour?
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
SW = 77.0

f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
total = 0; hits = []
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    try:
        ops = m_barple.find(C, SW)
    except Exception:
        continue
    if ops:
        total += 1
        if len(hits) < 25:
            hits.append(chr(cp))
f.close()
print("m_barple 在 T6 上命中: %d 字" % total)
print("  " + "".join(hits))