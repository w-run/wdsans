#!/usr/bin/env python3
"""trace_yong - trace 永 c4 closure gap through all build stages"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',   B+'masters_T6/master-Regular-400.otf'),
  ('MOD',  B+'masters_MOD/master-Regular-400.otf'),
  ('R1',   B+'masters_R1/master-Regular-400.otf'),
  ('R2',   B+'masters_R2/master-Regular-400.otf'),
  ('R4',   B+'masters_R4/master-Regular-400.otf'),
  ('R10',  B+'masters_R10/master-Regular-400.otf'),
  ('R15',  B+'masters_R15/master-Regular-400.otf'),
  ('R29',  B+'masters_R29/master-Regular-400.otf'),
  ('R30',  B+'masters_R30/master-Regular-400.otf'),
]


def yong_contours(path, decomp=False):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = DecomposingRecordingPen(gs) if decomp else RecordingPen()
    gs[cm[ord("永")]].draw(rp); f.close()
    return contours_from_pen(rp.value)


print("%-6s %-4s %s" % ("stage", "n", "contour closures (start -> end, gap)"))
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    C = yong_contours(p)
    parts = []
    for ci, c in enumerate(C):
        segs = c["segs"]
        if len(segs) < 4:
            continue
        st = np.array(c["start"], float)
        last = np.array(segs[-1][-1], float)
        gap = float(np.hypot(*(last - st)))
        if gap < 0.9:
            continue
        parts.append("c%d(%.0f,%.0f)->(%.0f,%.0f) gap=%.1f" % (
            ci, st[0], st[1], last[0], last[1], gap))
    print("  %-6s %-4d %s" % (lbl, len(C), " | ".join(parts) if parts else "(all closed)"))