#!/usr/bin/env python3
# seam_yong - find which contour seams have gaps in 永
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R30/'
FS = [('250','master-ExtraLight-250.otf'), ('400','master-Regular-400.otf'), ('900','master-Heavy-900.otf')]


def endp(s):
    if s[0] == "QM":
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def dump(path):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
    return contours_from_pen(rp.value)


for tag, fn in FS:
    C = dump(B + fn)
    print("=== %s: %d contours ===" % (tag, len(C)))
    for ci, c in enumerate(C):
        segs = c["segs"]
        st = np.array(c["start"], float)
        e = endp(segs[-1])
        gap = float(np.hypot(*(e - st)))
        sig = "".join(s[0] for s in segs)
        flag = "  <== UNCLOSED %.1f" % gap if gap > 0.9 else ""
        print("  c%d %-9s start(%7.1f,%7.1f) end(%7.1f,%7.1f)%s" % (
            ci, sig, st[0], st[1], e[0], e[1], flag))
    print()