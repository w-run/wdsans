#!/usr/bin/env python3
# invert_scan - how many barple glyphs have the bar-vs-slant order inverted?
#
# SHS correct pattern: slant rightmost  >  bar right end
# Our barple:          bar right end    >= slant rightmost  (inverted)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T6  = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
MOD = '/workspace/wdsans2/build/masters_MOD/master-Regular-400.otf'
SW = 77.0


def geom(path, cp):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if cp not in cm:
        f.close(); return None, None
    rp = RecordingPen(); gs[cm[cp]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    bar = None; slant = None
    for c in C:
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
        sig = "".join(s[0] for s in c["segs"])
        if sig == "LLL" and len(c["segs"]) == 3:
            w = P[:,0].max()-P[:,0].min(); h = P[:,1].max()-P[:,1].min()
            if w >= 1.5*SW and h <= 2.5*SW:
                bar = P[:,0].max()
        if len(c["segs"]) >= 4 and P[:,0].max() > (bar or 0) - 200:
            if slant is None or P[:,0].max() > slant:
                slant = P[:,0].max()
    return bar, slant


f = TTFont(T6, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
hits = []
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    try:
        if m_barple.find(C, SW):
            hits.append(cp)
    except Exception:
        pass
f.close()

print("barple hits: %d glyphs, sampling 400..." % len(hits))
import random
random.seed(0)
samp = random.sample(hits, min(400, len(hits)))

inverted = []
for cp in samp:
    b6, s6 = geom(T6, cp)
    bm, sm = geom(MOD, cp)
    if None in (b6, s6, bm, sm):
        continue
    before = "slant>" if s6 > b6 else "bar>="
    after  = "slant>" if sm > bm else "bar>="
    if before == "slant>" and after == "bar>=":
        inverted.append(chr(cp))
print()
print("T6 正确(slant>bar) -> MOD 反转(bar>=slant): %d / %d" % (len(inverted), len(samp)))
print("  " + "".join(inverted[:40]))