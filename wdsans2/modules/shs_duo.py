#!/usr/bin/env python3
# shs_duo - dump SHS 多 c0 16-seg path to see how bar meets slant
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

f = TTFont('/workspace/wdsans/ref/shs/shs-250.otf', lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
C = contours_from_pen(rp.value)
c = C[0]
print("SHS 多 c0: %d segs" % len(c["segs"]))
print("起点 (%.1f, %.1f)" % (c["start"][0], c["start"][1]))
for k, s in enumerate(c["segs"]):
    e = s[-1]
    ex = ""
    if s[0] == "C": ex = "  c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
    elif s[0] == "Q": ex = "  c(%.0f,%.0f)" % (s[1][0],s[1][1])
    print("  %2d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], ex))