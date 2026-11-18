#!/usr/bin/env python3
# claim_check - does barple actually improve the 11 glyphs it claims to fix?
# Compare T6 vs R31 against SHS for: 永今亨夕多了互乳亂延各
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

T = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
R = '/workspace/wdsans2/build/masters_R31/master-Regular-400.otf'
S = '/workspace/wdsans/ref/shs/shs-400.otf'


def prof(path, ch, ys):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
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
            n = 20 if s[0] != "L" else 2
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
                if abs(q[1]-y) < 3.0:
                    if best is None or q[0] > best:
                        best = q[0]
        out.append(best)
    return out


ys = list(np.linspace(150, 800, 20))
print("%-4s %-10s %-10s %s" % ("char", "T6 err", "R31 err", "winner"))
t6w = 0; r31w = 0; tie = 0
for ch in "永今亨夕多了互乳亂延各":
    a = prof(S, ch, ys); b = prof(T, ch, ys); c = prof(R, ch, ys)
    if not a or not b or not c:
        print("  %s  skip" % ch); continue
    et = []; er = []
    for x, y, z in zip(a, b, c):
        if x is None: continue
        if y is not None: et.append(abs(y-x))
        if z is not None: er.append(abs(z-x))
    if not et or not er:
        print("  %s  skip" % ch); continue
    mt = sum(et)/len(et); mr = sum(er)/len(er)
    if mt < mr - 2:
        w = "T6"; t6w += 1
    elif mr < mt - 2:
        w = "R31"; r31w += 1
    else:
        w = "tie"; tie += 1
    print("%-4s %-10.1f %-10.1f %s" % (ch, mt, mr, w))
print("")
print("T6 better: %d   R31 better: %d   tie: %d" % (t6w, r31w, tie))