#!/usr/bin/env python3
'''
gap_v2 - correct closure test: last segment ENDPOINT vs path START
'''

My earlier script had a bug: for QM/poly segments segs[-1][-1] is not a
2-tuple coordinate, so numpy built garbage. Fix: use endp() helper.
"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

P = '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def endp(s):
    if s[0] == "QM":
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def gaps(path, ch):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
    for c in C:
        st = np.array(c["start"], float)
        try:
            last = endp(c["segs"][-1])
        except Exception:
            out.append("ERR"); continue
        out.append(round(float(np.hypot(*(last-st))), 1))
    return out


print("=== control group ===")
for lbl, path in [("我们", P), ("SHS", SHS)]:
    print(" %s:" % lbl)
    for ch in "口日田国回十中一永":
        print("   %s: %s" % (ch, gaps(path, ch)))

print()
print("=== full scan ===")
for lbl, path in [("R30", P), ("SHS", SHS)]:
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    bad = []
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
            if len(c["segs"]) < 3:
                continue
            st = np.array(c["start"], float)
            try:
                last = endp(c["segs"][-1])
            except Exception:
                continue
            g = float(np.hypot(*(last - st)))
            if 0.8 < g < 15.0:
                worst = max(worst, g)
        if worst > 0:
            bad.append((round(worst,1), chr(cp)))
    f.close()
    bad.sort(reverse=True)
    print("%s: %d / %d glyphs with 0.8~15 gap" % (lbl, len(bad), len(cjk)))
    print("  " + " ".join("%s%.1f" % (c, g) for g, c in bad[:25]))