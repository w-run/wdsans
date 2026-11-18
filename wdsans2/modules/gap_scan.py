#!/usr/bin/env python3
"""gap_scan - how many glyphs have an unclosed contour gap 1~10 units?"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

P = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'


def scan(path, label):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    bad = []
    tot = 0
    cjk = [cp for cp in cm if 0x4E00 <= cp <= 0x9FFF]
    for cp in cjk:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        worst = 0.0
        for c in C:
            segs = c["segs"]
            if len(segs) < 4:
                continue
            st = np.array(c["start"], float)
            last = np.array(segs[-1][-1], float)
            g = float(np.hypot(*(last - st)))
            if 0.8 < g < 12.0:
                worst = max(worst, g)
        if worst > 0:
            bad.append((round(worst,1), chr(cp)))
        tot += 1
    f.close()
    bad.sort(reverse=True)
    print("%s: %d / %d glyphs have 0.8~12 gap" % (label, len(bad), tot))
    print("  " + " ".join("%s%.1f" % (c, g) for g, c in bad[:30]))
    return bad


a = scan(P, "R30 400wt")
print()
b = scan("/workspace/wdsans/ref/shs/shs-400.otf", "SHS 400wt")