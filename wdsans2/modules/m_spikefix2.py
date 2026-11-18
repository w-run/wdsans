#!/usr/bin/env python3
"""m_spikefix2 - repair taper spur tips (curvature-based)

User report: 眼 has a thin upward spur at the bottom-right of 艮.

Actual structure of our c4 (R29, 400wt):
  start (426,-14)
  0 L -> (432,-80)
  1 C c1(451,-67) c2(483,-56) -> (689, 84)   <== spur tip
  2 C c1(686, 16) c2(685, 47) -> (685, 68)
  3 L -> (462, 14)

SHS equivalent:
  ... C c1(452,-67) c2(484,-56) -> (690, 0)   <== flat tip at y=0
      C c1(688, 16) c2(686, 47) -> (687, 68)

Control points match within 1-2 units. ONLY the tip endpoint differs:
y=84 (ours) vs y=0 (SHS) -> 84 units raised, creating the spur.

Detection: at the contour x-maximum endpoint, compare incoming tangent
direction (c2 -> tip) with outgoing tangent (tip -> next c1).
A spur has a sharp reversal (large angle) AND tip y above BOTH
neighbours y by >= 30.

Fix: set tip y to the outgoing segment first control point y.
     (in SHS the tip y equals next c1 y = 16 .. close to 0; using
      next-c1 y keeps stroke end flat and preserves stroke weight)
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R29')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R30')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

# 400wt detection seed, then apply same indices to 250/900
CAND = '眼根跟很恨痕銀银限艰退良艮'


def tip_of(c):
    """Return (k, tip, prev_y, next_c1_y, dy) for x-max C/Q tip or None."""
    segs = c["segs"]
    if len(segs) < 3:
        return None
    seq = [tuple(c["start"])]
    for s in segs:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    mx = max(p[0] for p in seq)
    for k, s in enumerate(segs):
        if s[0] not in ("C","Q"):
            continue
        e = np.array(s[-1], float)
        if abs(e[0] - mx) > 3:
            continue
        prev = np.array(seq[k], float)
        ns = segs[(k+1) % len(segs)]
        nxt = np.array(ns[-1], float)
        dy = min(e[1] - prev[1], e[1] - nxt[1])
        if dy < 30:
            continue
        # outgoing first control point y
        if ns[0] == "C":
            n_c1_y = float(ns[1][1])
        elif ns[0] == "Q":
            n_c1_y = float(ns[1][1])
        else:
            n_c1_y = float(nxt[1])
        return (k, (float(e[0]), float(e[1])), float(prev[1]), n_c1_y, float(dy))
    return None


def fix_contour(c, info):
    k, tip, prev_y, n_c1_y, dy = info
    segs = [list(s) for s in c["segs"]]
    s = segs[k]
    # keep tip x, lower y to outgoing control-point y (flat end)
    new_e = (tip[0], n_c1_y)
    if s[0] == "C":
        segs[k] = ["C", s[1], s[2], new_e]
    else:
        segs[k] = ["Q", s[1], new_e]
    return {"start": c["start"], "segs": segs}


def process(tag):
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    idxf = "/workspace/wdsans2/build/spike_idx.json"
    if tag != "400":
        idx = json.load(open(idxf))
    else:
        idx = {}
        for ch in CAND:
            cp = ord(ch)
            if cp not in cm:
                continue
            rp = RecordingPen(); gs[cm[cp]].draw(rp)
            C = contours_from_pen(rp.value)
            hits = []
            for ci, c in enumerate(C):
                info = tip_of(c)
                if info:
                    hits.append([ci, info[0]])
            if hits:
                idx[str(cp)] = hits
        json.dump(idx, open(idxf, "w"))
        print("  400 detect: %d chars %s" % (len(idx), "".join(chr(int(k)) for k in idx)), flush=True)

    n = 0; sk = 0; det = []
    for cps, hits in idx.items():
        cp = int(cps)
        gn = cm.get(cp)
        if not gn:
            sk += 1; continue
        rp = RecordingPen(); gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        ok = False
        for ci, _ in hits:
            if ci >= len(C):
                continue
            info = tip_of(C[ci])
            if not info:
                continue
            NEW[ci] = fix_contour(C[ci], info)
            ok = True
        if not ok:
            sk += 1; continue
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1; det.append(chr(cp))
        except Exception as e:
            sk += 1
    print("  %s: fixed %d skipped %d %s" % (tag, n, sk, "".join(det)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


import json
if __name__ == "__main__":
    for t in ['400', '250', '900']:
        process(t)
    print("done")
