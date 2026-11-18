#!/usr/bin/env python3
"""yong3w - measure 永 c4 closure gap at 250/400/900 + SHS"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R30/'
FS = [('250','master-ExtraLight-250.otf'), ('400','master-Regular-400.otf'),
      ('900','master-Heavy-900.otf'), ('SHS','/workspace/wdsans/ref/shs/shs-400.otf')]


for tag, fn in FS:
    p = fn if fn.startswith("/") else B + fn
    f = TTFont(p, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s (%d contours) ===" % (tag, len(C)))
    for ci, c in enumerate(C):
        segs = c["segs"]
        st = np.array(c["start"], float)
        last = np.array(segs[-1][-1], float)
        gap = float(np.hypot(*(last - st)))
        if gap < 0.9:
            continue
        # 只关心竖弯钩：轮廓高且起点在底部
        ys = [st[1]] + [float(np.array(s[-1], float)[1]) for s in segs]
        print("   c%d %dsegs  start(%.0f,%.0f) end(%.0f,%.0f)  gap=%.1f  dy=%.1f" % (
            ci, len(segs), st[0], st[1], last[0], last[1], gap, last[1]-st[1]))
    print()