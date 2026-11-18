#!/usr/bin/env python3
# duo_protrude - measure how much the bar juts out past the slant
#
# Slant c1 right edge descends from (743,736) to (770,685):
# so at any y in [685,736] the slant occupies x up to roughly
#   x_slant(y) = 770 + (y-685) * (743-770)/(736-685)
# The bar c2 spans the full y of its own thickness at x up to 770.
# Where bar covers y-range that the slant does not, the corner juts.
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R31/'
FN = {'250':'master-ExtraLight-250.otf','400':'master-Regular-400.otf','900':'master-Heavy-900.otf'}


def segs_of(c):
    out = []
    prev = np.array(c["start"], float)
    for s in c["segs"]:
        e = np.array(s[-1], float)
        if s[0] == "C":
            out.append((prev, np.array(s[1],float), np.array(s[2],float), e, "C"))
        elif s[0] == "Q":
            out.append((prev, np.array(s[1],float), None, e, "Q"))
        else:
            out.append((prev, None, None, e, "L"))
        prev = e
    return out


def x_at_y(segs, y):
    """rightmost x of contour at given y (sampled)"""
    best = None
    for p0, c1, c2, p1, t in segs:
        n = 60 if t != "L" else 2
        for i in range(n+1):
            u = i / n
            if t == "L":
                q = p0 + (p1-p0)*u
            elif t == "C":
                q = ((1-u)**3)*p0 + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*p1
            else:
                q = ((1-u)**2)*p0 + 2*(1-u)*u*c1 + (u**2)*p1
            if abs(q[1]-y) < 1.2:
                if best is None or q[0] > best:
                    best = q[0]
    return best


for tag in ["250","400","900"]:
    f = TTFont(B + FN[tag], lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("多")]].draw(rp); f.close()
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
        if sig == "LLL" and P[:,1].max() > 600 and P[:,0].max() > 700:
            bar = c
        elif sig == "LCCC" and P[:,0].max() > 700 and P[:,1].max() > 600:
            slant = c
    bs = segs_of(bar); ss = segs_of(slant)
    y0 = min(np.array([b[3][1] for b in ss] + [bar["start"][1]]))
    # bar y range
    bar_ys = [bar["start"][1]] + [s[-1][1] for s in bar["segs"]]
    print("=== %s ===" % tag)
    print("  bar y[%.0f,%.0f]  x_max=770" % (min(bar_ys), max(bar_ys)))
    for y in [min(bar_ys), (min(bar_ys)+max(bar_ys))/2, max(bar_ys)]:
        xs = x_at_y(ss, y)
        if xs is None:
            print("     y=%.0f  斜笔不在该高度  -> 横笔完全裸露，突出 770-? " % y)
        else:
            print("     y=%.0f  斜笔右缘 x=%.0f  横笔右端 770  突出=%.0f" % (y, xs, 770-xs))
    print()