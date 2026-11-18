#!/usr/bin/env python3
# m_seamfix - close small contour seams (endpoint != startpoint)
#
# User report: 永 vertical-hook outer edge shows a step/stair.
#
# Root cause: SHS ships 永 as 3 merged contours; our chain rebuilds the
# glyph as 7 independent stroke contours. Where a closed stroke wraps
# around, the last endpoint does not land exactly on the path start,
# leaving a 2-4 unit seam that renders as a visible step.
#
# Measured (contour c4 = vertical + hook, 8 segs):
#   250  start(517,-14)  end(517,-14)  gap 0.0   OK
#   400  start(543, 17)  end(546, 18)  gap 3.2   <-- the step
#   900  start(586, 68)  end(586, 68)  gap 0.0   OK
#
# Fix: for every contour whose gap is in (0.8, 8.0) - i.e. meant to be
# closed but off by a tiny amount - snap the final endpoint onto the
# path start. Pure coordinate move; segment count and operator types
# unchanged -> VF-safe.
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R30')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R31')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

GAP_LO = 0.8
GAP_HI = 8.0


def endp(s):
    if s[0] == "QM":
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def seam_of(c):
    """Return (k, gap) if contour c has a small closure seam, else None."""
    segs = c["segs"]
    if len(segs) < 3:
        return None
    st = np.array(c["start"], float)
    e = endp(segs[-1])
    gap = float(np.hypot(*(e - st)))
    if GAP_LO < gap < GAP_HI:
        return gap
    return None


def close_contour(c):
    """Snap final endpoint to path start."""
    segs = [list(s) for s in c["segs"]]
    st = tuple(float(v) for v in c["start"])
    last = segs[-1]
    if last[0] == "QM":
        pts = list(last[1])
        pts[-1] = st
        segs[-1] = ["QM", pts]
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
    cjk = [cp for cp in cm if 0x4E00 <= cp <= 0x9FFF]
    for cp in cjk:
        gn = cm[cp]
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        hits = []
        for ci, c in enumerate(C):
            g = seam_of(c)
            if g is not None:
                hits.append(ci)
        if not hits:
            continue
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        for ci in hits:
            NEW[ci] = close_contour(C[ci])
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1; ncont += len(hits)
            if len(det) < 12:
                det.append(chr(cp))
        except Exception:
            pass
    print("  %s: %d glyphs, %d contours closed  %s" % (tag, n, ncont, "".join(det)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


for t in ['400', '250', '900']:
    process(t)
print("done")