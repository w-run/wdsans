"""Latin merge v5: correct scaling + gvar rebuild incl. phantom points.

Bugs found by measurement in v4 (all in this file's history):
  1. inst_at() ignored sx/sy -> outlines stayed at Mona's natural width
     (measured: merged H ink width 583 vs 520, i.e. +12% designed-out).
  2. hmtx taken from Mona's DEFAULT instance (wght=200) instead of 400.
  3. the 4 trailing phantom points got zero deltas -> advance width frozen
     (measured: H advance 675 at both wght 250 and 900).

TrueType advance variation travels through gvar phantom points:
  pp1.x = xMin - lsb          (left side bearing origin)
  pp2.x = pp1.x + advanceWidth
so delta(pp1.x) = (xMin_w - lsb_w) - (xMin_b - lsb_b)
   delta(pp2.x) = delta(pp1.x) + (adv_w - adv_b)
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables import ttProgram

LATIN_MAX = 0x024F
PUNCT_RANGES = ((0x2000, 0x206F), (0x20A0, 0x20CF))


def _wanted(cp):
    return cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT_RANGES)


def simple_latin_map(mona):
    glyf = mona["glyf"]
    cm = mona.getBestCmap()
    return {cp: nm for cp, nm in cm.items()
            if _wanted(cp) and glyf[nm].numberOfContours >= 0}


def inst_at(mona_path, wght):
    return instancer.instantiateVariableFont(
        TTFont(mona_path), {"wght": wght, "wdth": 100, "opsz": 0},
        inplace=True, updateFontNames=False, optimize=False)


def scaled_coords(f, name, sx, sy):
    g = f["glyf"][name]
    if g.numberOfContours <= 0:
        return None
    return [(int(round(x * sx)), int(round(y * sy))) for x, y in g.coordinates]


def _xmin(coords):
    return min(p[0] for p in coords) if coords else 0


def merge(noto_path, mona_path, out_path, sx, sy):
    f = TTFont(noto_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    smap = simple_latin_map(m)
    todo = {cp: nm for cp, nm in smap.items() if cp in ncm}

    f400 = inst_at(mona_path, 400)
    f250 = inst_at(mona_path, 250)
    f900 = inst_at(mona_path, 900)

    glyf_f = f["glyf"]
    gv = f["gvar"]
    hmtx_f = f["hmtx"]

    replaced = 0
    skipped = []
    for cp, mname in todo.items():
        b = scaled_coords(f400, mname, sx, sy)
        lo = scaled_coords(f250, mname, sx, sy)
        hi = scaled_coords(f900, mname, sx, sy)
        if b is None or lo is None or hi is None:
            skipped.append((mname, "missing"))
            continue
        if len(b) != len(lo) or len(b) != len(hi):
            skipped.append((mname, "pt-mismatch"))
            continue

        g400 = f400["glyf"][mname]
        g = Glyph()
        g.numberOfContours = g400.numberOfContours
        g.coordinates = GlyphCoordinates(b)
        g.flags = list(g400.flags)
        g.endPtsOfContours = list(g400.endPtsOfContours)
        g.coordinates.toInt()
        g.program = ttProgram.Program()
        g.program.fromBytecode(b"")

        fname = ncm[cp]
        glyf_f[fname] = g

        adv_b, lsb_b = f400["hmtx"][mname]
        adv_lo, lsb_lo = f250["hmtx"][mname]
        adv_hi, lsb_hi = f900["hmtx"][mname]
        adv_b, lsb_b = int(round(adv_b * sx)), int(round(lsb_b * sx))
        adv_lo, lsb_lo = int(round(adv_lo * sx)), int(round(lsb_lo * sx))
        adv_hi, lsb_hi = int(round(adv_hi * sx)), int(round(lsb_hi * sx))
        hmtx_f[fname] = (adv_b, lsb_b)

        n = len(b)
        xm_b, xm_lo, xm_hi = _xmin(b), _xmin(lo), _xmin(hi)
        pp1_b, pp1_lo, pp1_hi = xm_b - lsb_b, xm_lo - lsb_lo, xm_hi - lsb_hi
        pp2_b, pp2_lo, pp2_hi = pp1_b + adv_b, pp1_lo + adv_lo, pp1_hi + adv_hi

        def deltas(other, other_xm, other_lsb, other_adv):
            oxm, olsb, oadv = other_xm, other_lsb, other_adv
            o_pp1 = oxm - olsb
            o_pp2 = o_pp1 + oadv
            d = [(other[i][0] - b[i][0], other[i][1] - b[i][1]) for i in range(n)]
            d.append((o_pp1 - pp1_b, 0))
            d.append((o_pp2 - pp2_b, 0))
            d.append((0, 0))
            d.append((0, 0))
            return d

        d900 = deltas(hi, xm_hi, lsb_hi, adv_hi)
        d250 = deltas(lo, xm_lo, lsb_lo, adv_lo)

        gv.variations[fname] = [
            TupleVariation({"wght": (0.0, 1.0, 1.0)}, d900),
            TupleVariation({"wght": (-1.0, -1.0, 0.0)}, d250),
        ]
        replaced += 1

    f.save(out_path)
    info = {"replaced": replaced, "skipped": len(skipped),
            "skip_sample": skipped[:6], "sx": round(sx, 4), "sy": round(sy, 4)}
    for x in (f, m, f400, f250, f900):
        try:
            x.close()
        except Exception:
            pass
    return info
