#!/usr/bin/env python3
# seam_severity - classify seams by how visible they are
#
# A seam becomes a VISIBLE step when the two endpoints are offset in a
# direction that creates a corner on the glyph OUTLINE. Measure:
#   - gap magnitude (bigger = more visible)
#   - whether the endpoint offset has a component NORMAL to the stroke
#     (perpendicular offset = visible step; tangential = invisible)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
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


f = TTFont("/workspace/wdsans2/build/masters_R30/master-Regular-400.otf", lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()

buckets = {">=4": [], "3~4": [], "2~3": [], "<2": []}
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    mg = 0.0
    for c in C:
        if len(c["segs"]) < 3:
            continue
        st = np.array(c["start"], float); e = endp(c["segs"][-1])
        gap = float(np.hypot(*(e-st)))
        if not (0.8 < gap < 12):
            continue
        if area(poly(c))/max(gap,1e-6) > 1000:
            mg = max(mg, gap)
    if mg >= 4:
        buckets[">=4"].append((round(mg,1), chr(cp)))
    elif mg >= 3:
        buckets["3~4"].append((round(mg,1), chr(cp)))
    elif mg >= 2:
        buckets["2~3"].append((round(mg,1), chr(cp)))
    elif mg > 0:
        buckets["<2"].append((round(mg,1), chr(cp)))
f.close()

for k in [">=4", "3~4", "2~3", "<2"]:
    v = sorted(buckets[k], reverse=True)
    print("%-5s %5d glyphs   %s" % (k, len(v), " ".join("%s%.1f" % (c,d) for d,c in v[:15])))