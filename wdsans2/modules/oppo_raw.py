#!/usr/bin/env python3
# oppo_raw - dump OPPO 多 raw path ops (QM segments)
import sys
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

f = TTFont("/workspace/wdsans/ref/ops/ops-400.ttf")
gs = f.getGlyphSet(); cm = f.getBestCmap()
gn = cm[ord("多")]
print("glyph name:", gn)
rp = RecordingPen()
gs[gn].draw(rp)
f.close()
print("ops:", len(rp.value))
for i, (op, args) in enumerate(rp.value):
    if op == "closePath":
        print("  %2d %s" % (i, op)); continue
    if op == "moveTo":
        print("  %2d moveTo (%.0f,%.0f)" % (i, args[0][0], args[0][1])); continue
    if op == "lineTo":
        print("  %2d lineTo (%.0f,%.0f)" % (i, args[0][0], args[0][1])); continue
    if op == "qCurveTo":
        pts = " ".join("(%.0f,%.0f)" % (p[0],p[1]) if p else "None" for p in args)
        print("  %2d qCurveTo %s" % (i, pts)); continue
    print("  %2d %s %s" % (i, op, args))