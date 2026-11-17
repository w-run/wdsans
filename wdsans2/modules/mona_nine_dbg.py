#!/usr/bin/env python3
"""mona_nine_dbg - 查 Mona 的 9 到底怎么取轮廓"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'
f = TTFont(MONA)
f = instantiateVariableFont(f, {"wght": 400}, inplace=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
gn = cm[ord("9")]
print("glyph 名:", gn)
print("advance:", f["hmtx"][gn][0])
print("是否复合:", gs[gn].numberOfContours if hasattr(gs[gn], "numberOfContours") else "?")

rp1 = RecordingPen(); gs[gn].draw(rp1)
print("RecordingPen ops:", len(rp1.value))
if rp1.value:
    print("  首 3:", rp1.value[:3])

rp2 = DecomposingRecordingPen(gs); gs[gn].draw(rp2)
print("Decomposing ops:", len(rp2.value))
if rp2.value:
    print("  首 3:", rp2.value[:3])

C1 = contours_from_pen(rp1.value)
C2 = contours_from_pen(rp2.value)
print("contours from rp1:", len(C1))
print("contours from rp2:", len(C2))
f.close()