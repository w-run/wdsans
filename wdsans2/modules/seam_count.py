#!/usr/bin/env python3
# seam_count - how many glyphs/contours REALLY have closure seams
# and compare against SHS (does SHS have them too?)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:,0]; y = P[:,1]
    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))


def scan(path, label, decomp=False):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    ng = 0; nc = 0; tot = 0; samples = []
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = DecomposingRecordingPen(gs) if decomp else RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        k = 0
        for c in C:
            if len(c["segs"]) < 3:
                continue
            st = np.array(c["start"], float); e = endp(c["segs"][-1])
            gap = float(np.hypot(*(e-st)))
            if not (0.8 < gap < 12):
                continue
            A = area(poly(c))
            if A/max(gap,1e-6) > 1000:
                k += 1
        tot += 1
        if k:
            ng += 1; nc += k
            if len(samples) < 10:
                samples.append(chr(cp))
    f.close()
    print("%-10s %5d/%5d glyphs, %6d contours  %s" % (label, ng, tot, nc, "".join(samples)))
    return ng


a = scan("/workspace/wdsans2/build/masters_R30/master-Regular-400.otf", "R30 400")
b = scan("/workspace/wdsans/ref/shs/shs-400.otf", "SHS 400", True)
c = scan("/workspace/wdsans/ref/hos/hos-400.ttf", "HOS 400", True)