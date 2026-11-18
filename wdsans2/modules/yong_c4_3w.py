#!/usr/bin/env python3
"""yong_c4_3w - dump 永 c4 (the vertical-hook contour) at all weights"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R30/'
FS = [('250','master-ExtraLight-250.otf'), ('400','master-Regular-400.otf'),
      ('900','master-Heavy-900.otf')]


def find_hook(C):
    """the vertical + hook contour: tallest, contains a V-down then curve"""
    best = None
    for ci, c in enumerate(C):
        pts = [np.array(c["start"], float)]
        for s in c["segs"]:
            if s[0] == "QM":
                for q in s[1]: pts.append(np.array(q, float))
            elif s[0] == "C":
                pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
            elif s[0] == "Q":
                pts.extend([np.array(s[1],float), np.array(s[2],float)])
            else:
                pts.append(np.array(s[1], float))
        P = np.array(pts)
        h = P[:,1].max() - P[:,1].min()
        if len(c["segs"]) >= 6 and (best is None or h > best[0]):
            best = (h, ci)
    return best[1] if best else None


for tag, fn in FS:
    f = TTFont(B + fn, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    ci = find_hook(C)
    c = C[ci]
    st = np.array(c["start"], float)
    last = np.array(c["segs"][-1][-1], float)
    print("=== %s  c%d  %dsegs ===" % (tag, ci, len(c["segs"])))
    print("   start (%.1f, %.1f)   end (%.1f, %.1f)   gap=%.1f" % (
        st[0], st[1], last[0], last[1], float(np.hypot(*(last-st)))))
    print("   cmds:", "".join(s[0] for s in c["segs"]))
    for k, s in enumerate(c["segs"]):
        e = s[-1]
        extra = ""
        if s[0] == "C": extra = "  c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
        elif s[0] == "Q": extra = "  c(%.0f,%.0f)" % (s[1][0],s[1][1])
        print("     %d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], extra))
    print()