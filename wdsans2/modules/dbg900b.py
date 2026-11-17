#!/usr/bin/env python3
"""dbg900b - why do 6 chars miss at 900wt"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/masters_R29/'
FS = [('250','master-ExtraLight-250.otf'), ('400','master-Regular-400.otf'), ('900','master-Heavy-900.otf')]


for tag, fn in FS:
    f = TTFont(B + fn, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    print("=== %s ===" % tag)
    for ch in "跟很银限艰退":
        rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp)
        C = contours_from_pen(rp.value)
        got = []
        for ci, c in enumerate(C):
            segs = c["segs"]
            if len(segs) < 3:
                continue
            seq = [tuple(c["start"])]
            for s in segs:
                if s[0] == "QM": seq.append(tuple(s[1][-1]))
                elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
                else: seq.append(tuple(s[1]))
            mx = max(p[0] for p in seq)
            for k, s in enumerate(segs):
                if s[0] not in ("C","Q"):
                    continue
                e = s[-1]
                if abs(e[0] - mx) > 5:
                    continue
                prev = np.array(seq[k], float)
                rise = float(e[1] - prev[1])
                ns = segs[(k+1) % len(segs)]
                ty = float(ns[1][1]) if ns[0] in ("C","Q") else float(np.array(ns[-1], float)[1])
                drop = float(e[1] - ty)
                got.append("c%d k%d rise=%.0f drop=%.0f" % (ci, k, rise, drop))
        print("  %s: %s" % (ch, ", ".join(got) if got else "no x-max tip"))
    f.close()