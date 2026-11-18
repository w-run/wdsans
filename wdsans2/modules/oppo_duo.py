#!/usr/bin/env python3
# oppo_duo - dump OPPO 多 junction to learn the target shape
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def dump(path, lbl, ch="多"):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("%s: no glyph" % lbl); f.close(); return
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s (%d contours) ===" % (lbl, len(C)))
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
        if P[:,1].max() < 550 or P[:,0].max() < 600:
            continue
        sig = "".join(s[0] for s in c["segs"])
        print("  c%d %-14s x[%.0f,%.0f] y[%.0f,%.0f]" % (ci, sig, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
        print("     起点 (%.1f,%.1f)" % (c["start"][0], c["start"][1]))
        for k, s in enumerate(c["segs"]):
            e = s[-1]
            ex = ""
            if s[0] in ("C","Q"):
                ex = "  " + " ".join("(%.0f,%.0f)" % (q[0],q[1]) for q in s[1:-1])
            print("        %d %-2s -> (%7.1f,%7.1f)%s" % (k, s[0], e[0], e[1], ex))
    print()


dump("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO 400")
dump("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", "R31 400")