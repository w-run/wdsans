#!/usr/bin/env python3
# trial_250 - build 250/400/900 variants and compare shapes numerically
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
T = '/workspace/wdsans2/build/masters_T6/'
S = '/workspace/wdsans/ref/shs/'
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
SN = {'250':'shs-250.otf','400':'shs-400.otf','900':'shs-900.otf'}


def prof(path, ch, y):
    """rightmost x at height y"""
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    best = None
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            n = 80 if s[0] != "L" else 2
            for i in range(n+1):
                u = i/n
                if s[0] == "L":
                    q = prev + (e-prev)*u
                elif s[0] == "C":
                    c1 = np.array(s[1],float); c2 = np.array(s[2],float)
                    q = ((1-u)**3)*prev + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*e
                else:
                    c1 = np.array(s[1],float)
                    q = ((1-u)**2)*prev + 2*(1-u)*u*c1 + (u**2)*e
                if abs(q[1]-y) < 2.0:
                    if best is None or q[0] > best:
                        best = q[0]
            prev = e
    return best


print("%-5s %-8s %-12s %-12s %-12s" % ("wt", "y", "R31", "T6", "SHS"))
for tag in ["250","400","900"]:
    for y in [700, 660, 620]:
        a = prof(B+FN[tag], "多", y)
        b = prof(T+FN[tag], "多", y)
        c = prof(S+SN[tag], "多", y)
        fa = "%.0f" % a if a else "-"
        fb = "%.0f" % b if b else "-"
        fc = "%.0f" % c if c else "-"
        print("%-5s %-8d %-12s %-12s %-12s" % (tag, y, fa, fb, fc))