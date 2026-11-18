#!/usr/bin/env python3
# test_snap - snap 永 c4 endpoint to start in a single glyph, render before/after
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
from PIL import Image, ImageDraw, ImageFont

SRC = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'
OUT = '/workspace/wdsans2/build/test_snap_400.otf'


f = TTFont(SRC)
gs = f.getGlyphSet(); cm = f.getBestCmap()
cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
gn = cm[ord("永")]
rp = RecordingPen(); gs[gn].draw(rp)
C = contours_from_pen(rp.value)

print("before:")
for ci, c in enumerate(C):
    st = np.array(c["start"], float)
    last = np.array(c["segs"][-1][1][-1] if c["segs"][-1][0] == "QM" else c["segs"][-1][-1], float)
    print("  c%d segs=%d gap=%.1f" % (ci, len(c["segs"]), float(np.hypot(*(last-st)))))

NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
# snap c4 (the hook) endpoint to its start
c = C[4]
st = tuple(float(v) for v in c["start"])
segs = [list(s) for s in c["segs"]]
last = segs[-1]
if last[0] == "C":
    segs[-1] = ["C", last[1], last[2], st]
NEW[4] = {"start": c["start"], "segs": segs}

old = csT[gn]
csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
f["post"].formatType = 3.0
f["post"].glyphOrder = None
f.save(OUT)
f.close()

print("after:")
f2 = TTFont(OUT, lazy=True); gs2 = f2.getGlyphSet(); cm2 = f2.getBestCmap()
rp2 = RecordingPen(); gs2[cm2[ord("永")]].draw(rp2); f2.close()
C2 = contours_from_pen(rp2.value)
for ci, c in enumerate(C2):
    st = np.array(c["start"], float)
    last = np.array(c["segs"][-1][1][-1] if c["segs"][-1][0] == "QM" else c["segs"][-1][-1], float)
    print("  c%d segs=%d gap=%.1f" % (ci, len(c["segs"]), float(np.hypot(*(last-st)))))

# render both at high zoom
SZ = 700
for lbl, path in [("before", SRC), ("after", OUT)]:
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 255)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "永", fill=0, font=ft)
    img.save("/workspace/wdsans2/build/snap_%s.png" % lbl)
    print("saved snap_%s.png" % lbl)