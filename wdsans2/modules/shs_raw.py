#!/usr/bin/env python3
# shs_raw - check SHS 永 real contour count via multiple pens
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from fontTools.pens.boundsPen import BoundsPen

SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
P30 = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'

for lbl, p in [("SHS", SHS), ("R30", P30)]:
    f = TTFont(p, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord("永")]
    for pencls, nm in [(RecordingPen, "RecordingPen"), (DecomposingRecordingPen, "Decomposing")]:
        rp = pencls(gs) if nm == "Decomposing" else pencls()
        gs[gn].draw(rp)
        moves = sum(1 for op, a in rp.value if op == "moveTo")
        comps = sum(1 for op, a in rp.value if op == "addComponent")
        print("  %-4s %-14s ops=%-4d moveTo=%d addComponent=%d" % (lbl, nm, len(rp.value), moves, comps))
    print()
    f.close()