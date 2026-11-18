#!/usr/bin/env python3
"""m_spikefix4 - repair taper spur tips, weight-calibrated

User report: 眼 has a thin upward spur at bottom-right of 艮.

Measured spur geometry, c4 of 眼 across weights:
  250: tip seg1 (686,13)  rise=81,  then seg2 (684,40) rise=27 <- real spur
  400: tip seg1 (689,84)  rise=164 <- real spur
  900: tip seg1 (698,57)  rise=157 <- real spur

SHS reference tip y = 0 (400wt). Our tip is 84 higher -> spur.

Key insight: the spur is the LAST local y-maximum on the contour at
its x-extreme. Rather than a fixed rise threshold, look for an
endpoint at x-max whose y exceeds the OUTGOING control point y by
more than 20 units AND whose incoming rise is >= 25. Then lower the
tip to the outgoing control point y (flattening the spur).

Weight handling: 400 drives detection; the same (contour, seg) index
is applied to 250/900 so topology stays identical (VF requirement).
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
RISE_MIN = {250: 20.0, 400: 25.0, 900: 25.0}
DROP_MIN = 18.0


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


def find_tip(c, tag):
    """Return (k, ex, ey, target_y) for the spur tip, or None."""
    segs = c["segs"]
    if len(segs) < 3:
        return None
    seq = seqpts(c)
    mx = max(p[0] for p in seq)
    best = None
    for k, s in enumerate(segs):
        if s[0] not in ("C","Q"):
            continue
        e = np.array(s[-1], float)
        if abs(e[0] - mx) > 5:
            continue
        prev = np.array(seq[k], float)
        rise = float(e[1] - prev[1])
        if rise < RISE_MIN[tag]:
            continue
        ns = segs[(k+1) % len(segs)]
        ty = float(ns[1][1]) if ns[0] in ("C","Q") else float(np.array(ns[-1], float)[1])
        drop = float(e[1] - ty)
        if drop < DROP_MIN:
            continue
        if best is None or drop > best[3]:
            best = (k, float(e[0]), float(e[1]), drop, ty)
    if best is None:
        return None
    return (best[0], best[1], best[2], best[4])


def fix_contour(c, tip):
    k, ex, ey, ty = tip
    segs = [list(s) for s in c["segs"]]
    s = segs[k]
    new_e = (ex, ty)
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
    idxf = "/workspace/wdsans2/build/spike4_idx.json"
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
                if find_tip(c, 400):
                    hits.append(ci)
            if hits:
                idx[str(cp)] = hits
        json.dump(idx, open(idxf, "w"))
        print("  400 detect: %d chars -> %s" % (len(idx), "".join(chr(int(k)) for k in idx)), flush=True)

    n = 0; sk = 0; det = []
    t = int(tag)
    for cps, hits in idx.items():
        cp = int(cps)
        gn = cm.get(cp)
        if not gn:
            sk += 1; continue
        rp = RecordingPen(); gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        ok = False
        for ci in hits:
            if ci >= len(C):
                continue
            tip = find_tip(C[ci], t)
            if not tip:
                continue
            NEW[ci] = fix_contour(C[ci], tip)
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
