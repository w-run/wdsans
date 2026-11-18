#!/usr/bin/env python3
# which_closer - is T6 or R31 closer to SHS on the barple-hit glyphs?
#
# If T6 is systematically closer, barple is doing harm on those glyphs.
import sys, random
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import m_barple

T = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
R = '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf'
S = '/workspace/wdsans/ref/shs/shs-400.otf'
SW = 77.0


def prof(path, cp, ys):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if cp not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[cp]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    segs = []
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            segs.append((prev, s, e)); prev = e
    out = []
    for y in ys:
        best = None
        for prev, s, e in segs:
            n = 12 if s[0] != "L" else 2
            for k in range(n+1):
                u = k/n
                if s[0] == "L":
                    q = prev + (e-prev)*u
                elif s[0] == "C":
                    c1 = np.array(s[1],float); c2 = np.array(s[2],float)
                    q = ((1-u)**3)*prev + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*e
                else:
                    c1 = np.array(s[1],float)
                    q = ((1-u)**2)*prev + 2*(1-u)*u*c1 + (u**2)*e
                if abs(q[1]-y) < 4.0:
                    if best is None or q[0] > best:
                        best = q[0]
        out.append(best)
    return out


f = TTFont(T, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
hits = []
for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
    rp = RecordingPen()
    try:
        gs[cm[cp]].draw(rp)
    except Exception:
        continue
    try:
        if m_barple.find(contours_from_pen(rp.value), SW):
            hits.append(cp)
    except Exception:
        pass
f.close()
random.seed(1)
samp = random.sample(hits, 60)

ys = list(np.linspace(620, 800, 8))
t6_better = 0; r31_better = 0; tie = 0
ex = []
for cp in samp:
    a = prof(S, cp, ys)
    b = prof(T, cp, ys)
    c = prof(R, cp, ys)
    if not a or not b or not c:
        continue
    dt = []; dr = []
    for x, y, z in zip(a, b, c):
        if x is None:
            continue
        if y is not None:
            dt.append(abs(y-x))
        if z is not None:
            dr.append(abs(z-x))
    if not dt or not dr:
        continue
    mt = sum(dt)/len(dt); mr = sum(dr)/len(dr)
    if mt < mr - 3:
        t6_better += 1
        if len(ex) < 12:
            ex.append("%s(%.0f<%.0f)" % (chr(cp), mt, mr))
    elif mr < mt - 3:
        r31_better += 1
    else:
        tie += 1

print("barple 命中抽样 %d 字" % len(samp))
print("  T6 更接近 SHS: %d" % t6_better)
print("  R31 更接近 SHS: %d" % r31_better)
print("  tie: %d" % tie)
print("  例: " + " ".join(ex))