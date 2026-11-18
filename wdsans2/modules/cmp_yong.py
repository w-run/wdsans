#!/usr/bin/env python3
# cmp_yong - side by side contour dump SHS vs R30 for 永
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

FS = [('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
      ('R30', '/workspace/wdsans2/build/masters_R30/master-Regular-400.otf')]


import re


def dump(path):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
    out = []
    cur = None
    for op, args in rp.value:
        if op == "moveTo":
            if cur: out.append(cur)
            cur = {"start": tuple(args[0]), "segs": []}
        elif op in ("lineTo", "curveTo", "qCurveTo"):
            if cur is not None:
                cur["segs"].append((op, args))
        elif op == "closePath":
            if cur: out.append(cur)
            cur = None
    if cur: out.append(cur)
    return out


def allpts(c):
    P = [np.array(c["start"], float)]
    for op, args in c["segs"]:
        for a in args:
            if hasattr(a, "__len__") and len(a) == 2:
                P.append(np.array(a, float))
    return np.array(P)


for lbl, p in FS:
    C = dump(p)
    print("=== %s: %d contours ===" % (lbl, len(C)))
    for i, c in enumerate(C):
        P = allpts(c)
        sig = "".join("C" if o == "curveTo" else "Q" if o == "qCurveTo" else "L" for o, a in c["segs"])
        print("  c%d  %-14s x[%5.0f,%5.0f] y[%5.0f,%5.0f]  start(%.0f,%.0f)" % (
            i, sig, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(),
            c["start"][0], c["start"][1]))
    print()