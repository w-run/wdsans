#!/usr/bin/env python3
"""spike2 - find tips raised vs SHS by matching contour topology"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import DecomposingRecordingPen
from canonpen3 import contours_from_pen

R29 = '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def narrow_pts(path):
    """Collect points that form a narrow spur: locally extreme in x but short."""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = DecomposingRecordingPen(gs)
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        segs = []
        for c in C:
            seq = [np.array(c["start"], float)]
            for s in c["segs"]:
                if s[0] == "QM": seq.append(np.array(s[1][-1], float))
                elif s[0] in ("C","Q"): seq.append(np.array(s[-1], float))
                else: seq.append(np.array(s[1], float))
            for i in range(len(seq)):
                segs.append((seq[i], seq[(i+1) % len(seq)]))
        out[cp] = segs
    f.close()
    return out


def shape_score(segs):
    """count very short segments (<25 units) among long neighbours"""
    n = 0
    for a, b in segs:
        d = float(np.hypot(*(b - a)))
        if d < 25:
            n += 1
    return n


print('R29...', flush=True)
A = narrow_pts(R29)
print('SHS...', flush=True)
B = narrow_pts(SHS)

res = []
for cp in A:
    if cp not in B:
        continue
    sa, sb = shape_score(A[cp]), shape_score(B[cp])
    if sa > sb + 1:
        res.append((sa - sb, chr(cp)))
res.sort(reverse=True)
print()
print('R29 has more ultra-short segments than SHS: %d glyphs' % len(res))
print('  ' + ' '.join('%s+%d' % (c, d) for d, c in res[:40]))
print()
for ch in '眼贝真目':
    cp = ord(ch)
    if cp in A and cp in B:
        print('  %s  R29 short=%d  SHS short=%d' % (ch, shape_score(A[cp]), shape_score(B[cp])))