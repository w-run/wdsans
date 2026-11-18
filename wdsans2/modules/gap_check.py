#!/usr/bin/env python3
"""gap_check - validate: is the gap real? test control glyphs + bitmap"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

P = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


print("=== control group (should be simple closed shapes) ===")
for lbl, path in [("我们", P), ("SHS", SHS)]:
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    print(" %s:" % lbl)
    for ch in "口日田国回十中一":
        rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C = contours_from_pen(rp.value)
        gs2 = []
        for c in C:
            st = np.array(c["start"], float)
            last = np.array(c["segs"][-1][-1], float)
            gs2.append(round(float(np.hypot(*(last-st))),1))
        print("   %s: %d contours, gaps=%s" % (ch, len(C), gs2))
    f.close()

print()
print("=== does the gap show as ink? bitmap test on 永 hook corner ===")
from PIL import Image, ImageDraw, ImageFont
SZ = 1400
for lbl, path in [("我们", P), ("SHS", SHS)]:
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "永", fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    h, w = sub.shape
    # hook 外缘在右侧中部：x 0.52~0.56, y 0.75~0.85 (from bottom)
    band = sub[int(h*0.70):int(h*0.85), int(w*0.48):int(w*0.58)]
    print("  %s: hook band ink=%.1f%%  shape=%s" % (lbl, band.mean()*100, band.shape))