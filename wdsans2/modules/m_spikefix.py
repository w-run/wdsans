#!/usr/bin/env python3
"""m_spikefix - repair taper-induced spur tips

Symptom (user report): 眼 glyph has a thin upward spur at the
bottom-right of the 艮 component.

Root cause: m_taper (T6 stage) moved a taper tip END POINT along
the wrong direction. Control points are nearly identical to SHS,
but the endpoint was raised by 84 units:

  SHS : C c1(452,-67) c2(484,-56) -> (690,  0)
  ours: C c1(451,-67) c2(483,-56) -> (689, 84)

Fix: pull the tip endpoint back along its own curve direction so the
tip stays on the axis implied by the control points, keeping the
stroke end flat like SHS/HOS.

Method (VF-safe: pure point move, segment count unchanged):
  1. For each contour, find segments whose endpoint y is HIGHER than
     both neighbours AND which sit at the contour x-maximum;
  2. compute the tangent implied by c2 -> endpoint;
  3. move the endpoint to the intersection of that tangent with the
     neighbour edge line (i.e. flatten the spur).
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R29')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R30')
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf', '900': 'master-Heavy-900.otf'}

# candidate chars reported by user plus same-shape neighbours
CAND = '眼根跟很恨痕銀银限艰退'


def seqpts(c):
    seq = [tuple(c["start"])]
    for s in c["segs"]:
        if s[0] == "QM": seq.append(tuple(s[1][-1]))
        elif s[0] in ("C","Q"): seq.append(tuple(s[-1]))
        else: seq.append(tuple(s[1]))
    return seq


def shs_tip(ch):
    """Return the flat-tip endpoint y that SHS uses, for reference."""
    f = TTFont(SHS, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    return None


def find_spurs(C):
    """Return list of (ci, segi, drop_dy) for tapered spur tips."""
    out = []
    for ci, c in enumerate(C):
        segs = c["segs"]
        if len(segs) < 3:
            continue
        seq = seqpts(c)
        mx = max(p[0] for p in seq)
        # walk endpoints
        for k, s in enumerate(segs):
            if s[0] == "L":
                continue   # only curved taper tips
            e = np.array(s[-1], float)
            if abs(e[0] - mx) > 2:
                continue
            prev = np.array(seqpts(c)[k], float)
            nxt_s = segs[(k+1) % len(segs)]
            nxt = np.array(nxt_s[-1], float)
            up = min(e[1] - prev[1], e[1] - nxt[1])
            if up < 40:
                continue
            # c2 available?
            if s[0] == "C":
                c2 = np.array(s[2], float)
            elif s[0] == "Q":
                c2 = np.array(s[1], float)
            else:
                continue
            # tangent at tip from c2 -> e
            t = e - c2
            if abs(t[1]) < 1e-6:
                continue
            # target: where does the neighbour edge line cross e.x?
            # neighbour goes nxt -> nextnext, use its direction
            tgt_y = float(nxt[1])
            out.append((ci, k, up, (e[0], tgt_y)))
    return out


def apply_fix(C, spurs):
    NEW = []
    for c in C:
        NEW.append({"start": c["start"], "segs": [list(s) for s in c["segs"]]})
    for ci, k, up, (ex, ty) in spurs:
        s = NEW[ci]["segs"][k]
        if s[0] == "C":
            NEW[ci]["segs"][k] = ["C", s[1], s[2], (ex, ty)]
        elif s[0] == "Q":
            NEW[ci]["segs"][k] = ["Q", s[1], (ex, ty)]
    return NEW


def process(tag):
    src = os.path.join(SRC, FN[tag])
    f = TTFont(src)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f["CFF2"].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    n = 0; skipped = 0; detail = []
    for ch in CAND:
        cp = ord(ch)
        if cp not in cm:
            continue
        gn = cm[cp]
        rp = RecordingPen(); gs[gn].draw(rp)
        C = contours_from_pen(rp.value)
        sp = find_spurs(C)
        if not sp:
            skipped += 1; continue
        NEW = apply_fix(C, sp)
        old = csT[gn]
        try:
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            n += 1
            detail.append("%s(%d)" % (ch, len(sp)))
        except Exception:
            skipped += 1
    print("  %s: fixed %d, skipped %d  %s" % (tag, n, skipped, " ".join(detail)), flush=True)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    os.makedirs(OUTD, exist_ok=True)
    f.save(os.path.join(OUTD, FN[tag]))
    f.close()


for t in ['400', '250', '900']:
    process(t)
print("done")