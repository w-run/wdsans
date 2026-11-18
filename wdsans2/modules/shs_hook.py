#!/usr/bin/env python3
"""shs_hook - dump SHS 永 hook contour (18 segs) around the junction"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f = TTFont('/workspace/wdsans/ref/shs/shs-400.otf', lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
C = contours_from_pen(rp.value)
best = None
for ci, c in enumerate(C):
    if len(c["segs"]) >= 15:
        best = (ci, c)
ci, c = best
print("SHS hook contour c%d, %d segs" % (ci, len(c["segs"])))
print("  start (%.1f, %.1f)" % (c["start"][0], c["start"][1]))
for k, s in enumerate(c["segs"]):
    e = s[-1]
    extra = ""
    if s[0] == "C": extra = "  c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
    elif s[0] == "Q": extra = "  c(%.0f,%.0f)" % (s[1][0],s[1][1])
    elif s[0] == "QM":
        extra = "  " + str([(round(q[0]),round(q[1])) for q in s[1]])
    print("   %2d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], extra))