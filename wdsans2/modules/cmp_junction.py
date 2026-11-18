#!/usr/bin/env python3
# cmp_junction - side by side: SHS junction vs ours, T6 (pre-barple)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def show(path, lbl, want=None):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
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
        if P[:,1].max() < 600 or P[:,0].max() < 600:
            continue
        sig = "".join(s[0] for s in c["segs"])
        print("  c%d %-20s 起点(%.0f,%.0f) %d段" % (ci, sig, c["start"][0], c["start"][1], len(c["segs"])))
        print("     末3段:")
        for k in range(max(0, len(c["segs"])-3), len(c["segs"])):
            s = c["segs"][k]
            e = s[-1]
            ex = ""
            if s[0] == "C": ex = " c1(%.0f,%.0f) c2(%.0f,%.0f)" % (s[1][0],s[1][1],s[2][0],s[2][1])
            print("       %2d %-2s -> (%.1f,%.1f)%s" % (k, s[0], e[0], e[1], ex))
    print()

show("/workspace/wdsans/ref/shs/shs-400.otf", "SHS 400")
show("/workspace/wdsans2/build/masters_T6/master-Regular-400.otf", "T6 400 (pre-barple)")