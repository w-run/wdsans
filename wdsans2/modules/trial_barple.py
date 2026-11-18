#!/usr/bin/env python3
# trial_barple - build single-glyph variants for comparison
#
# Variants (400wt first):
#   A = T6 unmodified                  (pre-barple baseline)
#   B = T6 + current barple            (what we ship)
#   C = T6 + barple that KEEPS slant cut (proposed fix)
# Reference: SHS
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple

T6 = '/workspace/wdsans2/build/masters_T6/master-Regular-400.otf'
OUTD = '/workspace/wdsans2/build/trial'
SW = 77.0

CHAR = "多"


def is_slant_cut(body, ei):
    """Does body have a slant-cut segment right after ei?"""
    segs = body["segs"]
    if ei + 1 >= len(segs):
        return False
    nxt = segs[ei + 1]
    if nxt[0] != "L":
        return False
    p_prev = np.array(segs[ei][-1], float)
    p_end = np.array(nxt[1], float)
    dx = p_end[0] - p_prev[0]
    dy = p_end[1] - p_prev[1]
    L = float(np.hypot(dx, dy))
    if L < 0.3 * SW or L > 3.0 * SW:
        return False
    # slant cut: moves LEFT and UP (or mostly left) from a rightmost point
    return dx < -0.3 * L and abs(dy) < 1.5 * abs(dx)


def build(mode, char):
    f = TTFont(T6)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord(char)]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = m_barple.find(C, SW)
    if not hits:
        print("  %s: no barple hit" % char)
        f.close(); return None
    if mode == "A":
        f.close(); return None
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    applied = 0; skipped = 0
    for bi, ci, ei, xL, xR, by0 in hits:
        body = C[ci]
        if mode == "C" and is_slant_cut(body, ei):
            skipped += 1
            continue
        bar = NEW[bi]
        bar["start"] = (xR, bar["start"][1])
        s2 = bar["segs"][2]
        bar["segs"][2] = ["L", (xR, s2[-1][1])]
        nb = NEW[ci]
        if ei >= len(nb["segs"]):
            continue
        s = nb["segs"][ei]
        nb["segs"][ei] = ["C", s[1], s[2], (xR, by0)] if s[0] == "C" else ["L", (xR, by0)]
        del nb["segs"][ei+1:]
        applied += 1
    if applied == 0:
        print("  %s mode %s: all skipped (slant cut found)" % (char, mode))
        f.close(); return None
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    p = os.path.join(OUTD, "v%s.otf" % mode)
    f.save(p); f.close()
    print("  %s mode %s: applied=%d skipped=%d -> %s" % (char, mode, applied, skipped, p))
    return p


print("building variants for " + CHAR)
for m in ["B", "C"]:
    build(m, CHAR)
print("A = %s (untouched)" % T6)