#!/usr/bin/env python3
"""m_spikefix6 - repair taper spur tips with 400-driven index (VF-safe)

User report: 眼 has a thin upward spur at bottom-right of 艮.

Root cause: m_taper moved a taper tip endpoint upward. 400wt:
  SHS : C c1(452,-67) c2(484,-56) -> (690,  0)
  ours: C c1(451,-67) c2(483,-56) -> (689, 84)   <- 84 units raised

Per-weight contour c4 of 眼 differs in topology:
  400: seg1 ends (689, 84)  <- tip on seg1
  900: seg2 ends (692,111)  <- tip on seg2
  250: seg2 ends (684, 40)  <- tip on seg2, lower than its c2
so per-weight re-detection cannot be used (it rejects 250).

Solution: 400 drives detection -> records (contour index, segment
index). All three weights apply the fix at the SAME indices,
computing the target y from each weight own outgoing control point.
Only one endpoint coordinate moves -> segment count / operators
unchanged -> VF interpolation safe.
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R29')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R30')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}
CAND = '眼根跟很恨痕銀银限艰退良艮'


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


def detect(c):
    """400wt detection: return segment index of the spur tip, or None."""
    segs = c["segs"]
    if len(segs) < 3:
        return None
    seq = seqpts(c)
    mx = max(p[0] for p in seq)
    best = None
    for k, s in enumerate(segs):
        if s[0] not in ("C", "Q"):
            continue
        e = np.array(s[-1], float)
        if e[0] < mx - 20:
            continue
        prev = np.array(seq[k], float)
        if e[1] - prev[1] < 25:
            continue
        cy = float(s[2][1]) if s[0] == "C" else float(s[1][1])
        if e[1] - cy < 20:
            continue
        ns = segs[(k+1) % len(segs)]
        ty = float(ns[1][1]) if ns[0] in ("C","Q") else float(np.array(ns[-1], float)[1])
        if ty >= e[1] - 10:
            continue
        if best is None or e[1] > best[1]:
            best = (k, float(e[1]), ty)
    return best[0] if best else None


def apply_at(c, k):
    """Lower segment k endpoint to its outgoing control point y."""
    segs = [list(s) for s in c["segs"]]
    s = segs[k]
    ns = segs[(k+1) % len(segs)]
    ty = float(ns[1][1]) if ns[0] in ("C","Q") else float(np.array(ns[-1], float)[1])
    ex = float(s[-1][0])
    ey = float(s[-1][1])
    if ey - ty < 5:
        return None      # already flat at this weight
    if s[0] == "C":
        segs[k] = ["C", s[1], s[2], (ex, ty)]
    else:
        segs[k] = ["Q", s[1], (ex, ty)]
    return {"start": c["start"], "segs": segs}


def process(tag):
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    idxf = "/workspace/wdsans2/build/spike6_idx.json"
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
                k = detect(c)
                if k is not None:
                    hits.append([ci, k])
            if hits:
                idx[str(cp)] = hits
        json.dump(idx, open(idxf, "w"))
        print("  400 detect: %d chars -> %s" % (len(idx), "".join(chr(int(k)) for k in idx)), flush=True)

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
        for ci, k in hits:
            if ci >= len(C) or k >= len(C[ci]["segs"]):
                continue
            fixed = apply_at(C[ci], k)
            if fixed is None:
                continue
            NEW[ci] = fixed
            ok = True
        if not ok:
            sk += 1; continue
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1; det.append(chr(cp))
        except Exception:
            sk += 1
    print("  %s: fixed %d skipped %d %s" % (tag, n, sk, "".join(det)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


if __name__ == "__main__":
    for t in ['400', '250', '900']:
        process(t)
    print("done")
