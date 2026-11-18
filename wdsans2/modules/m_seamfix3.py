#!/usr/bin/env python3
# m_seamfix3 - close rounding seams (area-ratio criterion, validated)
#
# User report: 永 vertical-hook shows a step at high zoom.
#
# DIAGNOSIS (all measured on R30 400wt):
#  - SHS ships 永 as 3 merged contours; our chain rebuilds it as 7
#    independent stroke contours. Where a stroke wraps closed, the
#    final endpoint misses the path start by 1-11 units.
#  - Offset histogram is centred on 0 in BOTH axes:
#      dx median 0.00 mean -0.21, dy median 0.00 mean -0.15
#    -> pure integer-rounding residue from contour reconstruction,
#       not a systematic design offset.
#  - Severity: >=4 units 667 glyphs / 3-4 2196 / 2-3 13551 / <2 4065.
#    2.8 units = 0.28% em -> invisible at text sizes, visible only
#    when zoomed large (as the user did).
#
# DISCRIMINATOR (validated against control glyphs):
#    area / gap > 1000  => contour meant to be closed
#    口 ratios 222 / 689, 十 897 / 81, 一 916  -> all correctly skipped
#    永 c4 ratio 21019, 丁 c1 ratio 28260 -> correctly selected
#
# EARLIER BUGGY VERSIONS:
#   m_seamfix  used gap-only    -> hit 20468 glyphs (would weld strokes)
#   m_seamfix2 used area ratio but I mis-read its hit count as a bug;
#              the count 20479 is the REAL number of affected glyphs.
#
# Fix: snap the final endpoint onto the path start. One coordinate
# moves; segment count and operator types unchanged -> VF-safe.
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R30')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R31')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}
LIMIT = int(os.environ.get('WDS_LIMIT', '0'))   # 0 = all glyphs

GAP_LO = 0.8
GAP_HI = 12.0
RATIO_MIN = 1000.0


def endp(s):
    return np.array(s[1][-1], float) if s[0] == "QM" else np.array(s[-1], float)


def poly(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)


def area(P):
    x = P[:,0]; y = P[:,1]
    return 0.5*abs(float(np.dot(x, np.roll(y,1)) - np.dot(y, np.roll(x,1))))


def is_seam(c):
    if len(c["segs"]) < 3:
        return False
    st = np.array(c["start"], float)
    gap = float(np.hypot(*(endp(c["segs"][-1]) - st)))
    if not (GAP_LO < gap < GAP_HI):
        return False
    return (area(poly(c)) / max(gap, 1e-6)) > RATIO_MIN


def close_c(c):
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
    f = TTFont(os.path.join(SRC, FN[tag]))
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    n = 0; nc = 0
    cps = [c for c in cm if 0x4E00 <= c <= 0x9FFF]
    if LIMIT:
        cps = cps[:LIMIT]
    for cp in cps:
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
            NEW[ci] = close_c(C[ci])
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1; nc += len(hits)
        except Exception:
            pass
    print("  %s: %d glyphs, %d contours closed" % (tag, n, nc), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


for t in ['400', '250', '900']:
    process(t)
print("done")