#!/usr/bin/env python3
# rowscan - 逐行右缘, 只看上部横笔区域 (y em 640..780)
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

def right_at(path, ch, ys, qt=False):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm: f.close(); return {}
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    out = {}
    if qt:
        pts = []
        cur = None
        for op, args in rp.value:
            if op in ("moveTo","lineTo"):
                pts.append(np.array(args[0], float))
            elif op == "qCurveTo":
                for p in args:
                    if p: pts.append(np.array(p, float))
        pts = np.array(pts)
        for y in ys:
            sel = pts[np.abs(pts[:,1]-y) < 6]
            out[y] = sel[:,0].max() if len(sel) else None
        return out
    C = contours_from_pen(rp.value)
    segs = []
    for c in C:
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            segs.append((prev, s, e)); prev = e
    for y in ys:
        best = None
        for prev, s, e in segs:
            if s[0] == "L":
                for u in (0, 1):
                    q = prev + (e-prev)*u
                    if abs(q[1]-y) < 3:
                        if best is None or q[0] > best: best = q[0]
            elif s[0] == "C":
                c1 = np.array(s[1],float); c2 = np.array(s[2],float)
                for u in np.linspace(0,1,80):
                    q = ((1-u)**3)*prev + 3*((1-u)**2)*u*c1 + 3*(1-u)*(u**2)*c2 + (u**3)*e
                    if abs(q[1]-y) < 3:
                        if best is None or q[0] > best: best = q[0]
        out[y] = best
    return out

ys = list(range(660, 790, 10))
FONTS = [
  ("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf", True),
  ("T6  ", "/workspace/wdsans2/build/masters_T6/master-Regular-400.otf", False),
  ("P1b ", "/workspace/wdsans2/build/plan1b/B_400.otf", False),
  ("R31 ", "/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", False),
]
data = {}
for lbl, p, qt in FONTS:
    data[lbl] = right_at(p, "多", ys, qt)
print("y_em   " + "  ".join("%-6s" % l for l,_,_ in FONTS))
for y in ys:
    row = "  ".join("%-6s" % ("%.0f" % data[l][y] if data[l][y] else "-") for l,_,_ in FONTS)
    print("%-6d %s" % (y, row))