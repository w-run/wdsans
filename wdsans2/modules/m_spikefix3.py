#!/usr/bin/env python3
"""m_spikefix3 - repair taper spur tips (prev-only criterion)

User report: 眼 has a thin upward spur at bottom-right of 艮.

Measured geometry (400wt, c4 of 眼):
  R29: start(426,-14) L(432,-80) C c1(451,-67) c2(483,-56) -> (689, 84)
       then C c1(686,16) c2(685,47) -> (685,68)  then L(462,14)
  SHS: same control points, but tip is (690, 0)

The tip endpoint y is 84 higher than SHS -> thin spur.
Note: tip.y - next.y is only 16 (next point is also high), so a
symmetric criterion misses it. Use PREVIOUS point only:
  tip.y - prev.y = 84 - (-80) = 164  >= 60  -> detect

Fix: pull tip y down to the OUTGOING control point y (which in SHS
is 16, close to the flat end). This preserves stroke weight because
x is unchanged and only the spur height is removed.
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
RISE_MIN = 60.0


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


def tip_of(c):
    segs = c["segs"]
    if len(segs) < 3:
        return None
    seq = seqpts(c)
    mx = max(p[0] for p in seq)
    for k, s in enumerate(segs):
        if s[0] not in ("C","Q"):
            continue
        e = np.array(s[-1], float)
        if abs(e[0] - mx) > 3:
            continue
        prev = np.array(seq[k], float)
        rise = e[1] - prev[1]
        if rise < RISE_MIN:
            continue
        ns = segs[(k+1) % len(segs)]
        if ns[0] in ("C","Q"):
            target_y = float(ns[1][1])
        else:
            target_y = float(np.array(ns[-1], float)[1])
        if target_y >= e[1] - 5:
            continue   # no downward room -> not a spur
        return (k, float(e[0]), float(e[1]), float(target_y), float(rise))
    return None


def fix_contour(c, info):
    k, ex, ey, ty, rise = info
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
                if tip_of(c):
                    hits.append(ci)
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
        for ci in hits:
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
        except Exception:
            sk += 1
    print("  %s: fixed %d skipped %d %s" % (tag, n, sk, "".join(det)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


for t in ['400', '250', '900']:
    process(t)
print("done")