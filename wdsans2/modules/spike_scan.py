#!/usr/bin/env python3
"""spike_scan - scan library for taper spike artifacts

Criterion: a point P whose x equals the contour max x,
           P.y exceeds BOTH neighbours by >= 40,
           and distances to both neighbours are 25..220.
A glyph flagged here but not in SHS is a likely taper defect.
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R29 = '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def allseq(c):
    """返回按顺序的所有端点（start + 每段终点）"""
    seq = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            seq.append(np.array(s[1][-1], float))
        elif s[0] in ("C","Q"):
            seq.append(np.array(s[-1], float))
        else:
            seq.append(np.array(s[1], float))
    return seq


def spikes(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        n = 0
        for c in C:
            seq = allseq(c)
            if len(seq) < 4:
                continue
            mx = max(p[0] for p in seq)
            for i in range(1, len(seq) - 1):
                p, a, b = seq[i], seq[i-1], seq[i+1]
                if abs(p[0] - mx) > 1:
                    continue
                dy_up = min(p[1] - a[1], p[1] - b[1])
                if dy_up < 40:
                    continue
                d1 = np.hypot(*(p - a)); d2 = np.hypot(*(p - b))
                if not (25 <= d1 <= 220 and 25 <= d2 <= 220):
                    continue
                n += 1
        if n:
            out[cp] = n
    f.close()
    return out


print('扫描 R29...', flush=True)
A = spikes(R29)
print('扫描 SHS...', flush=True)
B = spikes(SHS)

only_us = {cp: n for cp, n in A.items() if cp not in B}
both = {cp: n for cp, n in A.items() if cp in B}
print()
print('仅我们有尖刺（疑似 taper 缺陷）: %d 字' % len(only_us))
items = sorted(only_us.items(), key=lambda x: -x[1])
print('  ' + ' '.join('%s%d' % (chr(cp), n) for cp, n in items[:40]))
print()
print('两家都有尖刺（设计特征，不动）: %d 字' % len(both))
print('  ' + ' '.join('%s%d' % (chr(cp), n) for cp, n in sorted(both.items(), key=lambda x:-x[1])[:20]))