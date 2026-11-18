#!/usr/bin/env python3
# trial_D - variant D: align bar to the SLANT CUT FACE, keep the cut segment
#
# Analysis so far:
#   A = T6 as-is          -> bar shorter than slant, notch below the bar
#   B = current barple    -> bar == xR (770), slant cut DELETED, bar sticks out
#   D = proposed          -> bar right edge follows the slant cut line,
#                            keep the cut segment so corner stays slanted.
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple

FN = {'250':'masters_T6/master-ExtraLight-250.otf','400':'masters_T6/master-Regular-400.otf','900':'masters_T6/master-Heavy-900.otf'}
BASE = '/workspace/wdsans2/build/'
OUTD = '/workspace/wdsans2/build/trial'
SW = {'250':30.0, '400':77.0, '900':150.0}


def build_D(char, tag):
    src = BASE + FN[tag]
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord(char)]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = m_barple.find(C, SW[tag])
    if not hits:
        print("  %s %s: no hit" % (char, tag))
        f.close(); return None
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    n_done = 0
    for bi, ci, ei, xL, xR, by0 in hits:
        body = C[ci]
        segs_b = body["segs"]
        # 斜切段 = ei 之后的第一个 L 段
        cut = None
        if ei + 1 < len(segs_b) and segs_b[ei+1][0] == "L":
            p0 = np.array(segs_b[ei][-1], float)
            p1 = np.array(segs_b[ei+1][1], float)
            L = float(np.hypot(*(p1-p0)))
            if 0.3*SW[tag] < L < 3.0*SW[tag] and (p1[0]-p0[0]) < -0.3*L:
                cut = (p0, p1)
        if cut is None:
            # 无斜切段 -> 保持原行为
            bar = NEW[bi]
            bar["start"] = (xR, bar["start"][1])
            bar["segs"][2] = ["L", (xR, bar["segs"][2][-1][1])]
            nb = NEW[ci]
            if ei < len(nb["segs"]):
                s = nb["segs"][ei]
                nb["segs"][ei] = ["C", s[1], s[2], (xR, by0)] if s[0] == "C" else ["L", (xR, by0)]
                del nb["segs"][ei+1:]
            n_done += 1
            continue
        # 有斜切段：横笔右端 = 斜切面在 bar 中线高度处的 x
        p0, p1 = cut
        bar = NEW[bi]
        bar_y0 = min(bar["start"][1], bar["segs"][2][-1][1])
        bar_y1 = max(bar["start"][1], bar["segs"][2][-1][1])
        ys_mid = (bar_y0 + bar_y1) / 2.0
        if abs(p1[1]-p0[1]) > 1e-6:
            t = (ys_mid - p0[1]) / (p1[1]-p0[1])
            t = max(0.0, min(1.0, t))
            x_at = p0[0] + t*(p1[0]-p0[0])
        else:
            x_at = min(p0[0], p1[0])
        # 横笔右端不超过 xR，也不短于原 bar 右端
        x_new = min(xR, max(x_at, max(np.array(bar["start"])[0], bar["segs"][2][-1][0])))
        bar["start"] = (x_new, bar["start"][1])
        bar["segs"][2] = ["L", (x_new, bar["segs"][2][-1][1])]
        # 斜笔：只把 ei 段终点顺到 (x_new, by0)，保留后面的斜切段
        nb = NEW[ci]
        s = nb["segs"][ei]
        nb["segs"][ei] = ["C", s[1], s[2], (x_new, by0)] if s[0] == "C" else ["L", (x_new, by0)]
        n_done += 1
    if n_done == 0:
        f.close(); return None
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    p = os.path.join(OUTD, "D_%s_%s.otf" % (char, tag))
    f.save(p); f.close()
    print("  %s %s: %d ops -> %s" % (char, tag, n_done, p))
    return p


for ch in "多及力刀":
    for t in ["250", "400", "900"]:
        build_D(ch, t)