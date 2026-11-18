#!/usr/bin/env python3
# m_seamfix2 - close contour seams, area-ratio criterion
#
# User report: 永 vertical-hook outer edge shows a step.
#
# PREVIOUS ATTEMPT (m_seamfix) WAS WRONG - do not use it:
#   it selected every contour with 0.8 < gap < 8.0, which matched
#   20,468 glyphs / 96,837 contours, because OPEN strokes (hangs,
#   pies) also have small-ish endpoint separations in some glyphs.
#   Closing those would have welded stroke ends into lines.
#
# CORRECT criterion: area / gap ratio.
#   A contour that is meant to be closed wraps a large area while its
#   endpoints are nearly coincident -> huge ratio.
#   An open stroke has two distant ends -> small ratio.
#
# Measured on 永 (400wt):
#   c0 gap 71.0 area 22791  ratio   321  -> open (stroke)
#   c2 gap  2.0 area 54231  ratio 27115  -> closed
#   c4 gap  3.2 area 66468  ratio 21019  -> closed  <-- the step
#   c6 gap 85.7 area 39200  ratio   457  -> open (stroke)
# Control 口: ratios 222 / 689  -> both open in our build (correct)
#
# Use RATIO_MIN = 1000 (3 orders of magnitude above open strokes).
# Fix: snap the final endpoint exactly onto the path start.
# Pure coordinate move, segment count unchanged -> VF-safe.
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R30')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R31')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

GAP_LO = 0.8      # below this it is already closed
GAP_HI = 12.0     # above this it is an open stroke
RATIO_MIN = 1000.0


def endp(s):
    if s[0] == "QM":
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]:
                P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1], float), np.array(s[2], float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:, 0]; y = P[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1))))


def is_seam(c):
    segs = c["segs"]
    if len(segs) < 3:
        return False
    st = np.array(c["start"], float)
    e = endp(segs[-1])
    gap = float(np.hypot(*(e - st)))
    if not (GAP_LO < gap < GAP_HI):
        return False
    A = area(poly(c))
    return (A / max(gap, 1e-6)) > RATIO_MIN


def close_contour(c):
    segs = [list(s) for s in c["segs"]]
    st = tuple(float(v) for v in c["start"])
    last = segs[-1]
    if last[0] == "QM":
        pts = list(last[1]); pts[-1] = st; segs[-1] = ["QM", pts]
    elif last[0] in ("C", "Q"):
        segs[-1] = [last[0]] + list(last[1:-1]) + [st]
    else:
        segs[-1] = ["L", st]
    return {"start": c["start"], "segs": segs}


def process(tag):
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    n = 0; ncont = 0; det = []
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        gn = cm[cp]
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        hits = [ci for ci, c in enumerate(C) if is_seam(c)]
        if not hits:
            continue
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        for ci in hits:
            NEW[ci] = close_contour(C[ci])
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1; ncont += len(hits)
            if len(det) < 20:
                det.append(chr(cp))
        except Exception:
            pass
    print("  %s: %d glyphs, %d contours  %s" % (tag, n, ncont, "".join(det)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


if __name__ == "__main__":
    for t in ['400', '250', '900']:
        process(t)
    print("done")
