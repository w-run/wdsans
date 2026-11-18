#!/usr/bin/env python3
# dev_scan - measure how far our right profile deviates from SHS
#
# This is the correct frame: SHS is the design reference for CJK.
# Walk 20 heights through the upper-right quadrant, compare rightmost x.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
S = '/workspace/wdsans/ref/shs/'
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}
SN = {'250':'shs-250.otf','400':'shs-400.otf','900':'shs-900.otf'}


def profile(path, ch, ymin, ymax, steps=24):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    segs = []
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            segs.append((prev, s, e))
            prev = e
    out = []
    for i in range(steps+1):
        y = ymin + (ymax-ymin)*i/steps
        best = None
        for prev, s, e in segs:
            n = 60 if s[0] != "L" else 2
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
                if abs(q[1]-y) < 2.5:
                    if best is None or q[0] > best:
                        best = q[0]
        out.append(best)
    return out


CH = "多及力刀九几乃予勇"
for tag in ["250","400","900"]:
    print("=== weight %s ===" % tag)
    bad = []
    for ch in CH:
        try:
            a = profile(B+FN[tag], ch, 550, 800)
            b = profile(S+SN[tag], ch, 550, 800)
        except Exception as ex:
            continue
        devs = []
        for x, y in zip(a, b):
            if x is None or y is None:
                continue
            devs.append(abs(x-y))
        if devs:
            m = max(devs); avg = sum(devs)/len(devs)
            flag = "  <<<" if m > 40 else ""
            print("  %s  max=%.0f  avg=%.0f%s" % (ch, m, avg, flag))
            if m > 40:
                bad.append(ch)
    print("  偏差>40 的字: %s" % ("".join(bad) if bad else "none"))
    print()