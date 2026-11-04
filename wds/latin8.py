"""Latin merge v8: composites by INLINING components (no new glyphs).

Hard constraint measured on our font: numGlyphs == 65535 (TrueType max).
So we cannot append component glyphs; v7 failed with
  struct.error: 'H' format requires 0 <= number <= 65535.

Trick: a composite glyph's outline can be flattened into a single simple
glyph by drawing the components through a DecomposingRecordingPen and
emitting one TTGlyphPen result. The codepoint still maps to one glyph, the
visual result is identical, and no extra glyph slots are consumed.

Variations still work because we flatten the SAME structure at 250/400/900
and rebuild gvar deltas for the flattened point set.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.misc.transform import Transform
from fontTools.ttLib.tables.TupleVariation import TupleVariation
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates
from fontTools.ttLib.tables import ttProgram


def _wanted(cp, LATIN_MAX=0x024F, PUNCT=((0x2000, 0x206F), (0x20A0, 0x20CF))):
    return cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT)


def flat_coords(font, name, sx, sy):
    """Flatten a (possibly composite) glyph to a point list, scaled."""
    gs = font.getGlyphSet()
    pen = DecomposingRecordingPen(gs)
    gs[name].draw(pen)
    tp = TTGlyphPen(None)
    p2 = TransformPen(tp, Transform(sx, 0, 0, sy, 0, 0))
    pen.replay(p2)
    g = tp.glyph()
    if g.numberOfContours <= 0:
        return None, None
    coords = [(int(round(x)), int(round(y))) for x, y in g.coordinates]
    return coords, g


def build(font_path, mona_path, out_path, sx, sy):
    from wds.latin5 import inst_at

    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    mcm = m.getBestCmap()

    f400 = inst_at(mona_path, 400)
    f250 = inst_at(mona_path, 250)
    f900 = inst_at(mona_path, 900)

    glyf_f = f["glyf"]
    gv = f["gvar"]
    hmtx_f = f["hmtx"]

    def is_comp(font, nm):
        return font["glyf"][nm].numberOfContours < 0

    targets = {}
    for cp, nm in mcm.items():
        if not _wanted(cp):
            continue
        if not is_comp(m, nm):
            continue
        if cp in ncm:
            targets[nm] = (cp, ncm[cp])
    # keep only those whose components are inside Mona's simple set
    simple_m = {nm for nm in m.getGlyphOrder()
                if m["glyf"][nm].numberOfContours >= 0}

    added = 0
    skipped = []
    for mname, (cp, fname) in targets.items():
        b, gb = flat_coords(f400, mname, sx, sy)
        lo, _ = flat_coords(f250, mname, sx, sy)
        hi, _ = flat_coords(f900, mname, sx, sy)
        if b is None or lo is None or hi is None:
            skipped.append((mname, "no-outline"))
            continue
        if len(b) != len(lo) or len(b) != len(hi):
            skipped.append((mname, "pt-mismatch"))
            continue

        glyf_f[fname] = gb
        adv, lsb = f400["hmtx"][mname]
        adv_lo, lsb_lo = f250["hmtx"][mname]
        adv_hi, lsb_hi = f900["hmtx"][mname]
        adv, lsb = int(round(adv * sx)), int(round(lsb * sx))
        adv_lo, lsb_lo = int(round(adv_lo * sx)), int(round(lsb_lo * sx))
        adv_hi, lsb_hi = int(round(adv_hi * sx)), int(round(lsb_hi * sx))
        hmtx_f[fname] = (adv, lsb)

        n = len(b)
        xm = lambda pts: min(p[0] for p in pts)
        xm_b, xm_lo, xm_hi = xm(b), xm(lo), xm(hi)
        pp1_b = xm_b - lsb
        pp2_b = pp1_b + adv
        o_pp1_hi = xm_hi - lsb_hi
        o_pp2_hi = o_pp1_hi + adv_hi
        o_pp1_lo = xm_lo - lsb_lo
        o_pp2_lo = o_pp1_lo + adv_lo

        def mk(other, oxm, olsb, oadv):
            o_pp1 = oxm - olsb
            o_pp2 = o_pp1 + oadv
            d = [(other[i][0] - b[i][0], other[i][1] - b[i][1]) for i in range(n)]
            d.append((o_pp1 - pp1_b, 0))
            d.append((o_pp2 - pp2_b, 0))
            d.append((0, 0))
            d.append((0, 0))
            return d

        gv.variations[fname] = [
            TupleVariation({"wght": (0.0, 1.0, 1.0)}, mk(hi, xm_hi, lsb_hi, adv_hi)),
            TupleVariation({"wght": (-1.0, -1.0, 0.0)}, mk(lo, xm_lo, lsb_lo, adv_lo)),
        ]
        added += 1

    f.save(out_path)
    info = {"added": added, "candidates": len(targets),
            "skipped": len(skipped), "sample": skipped[:8]}
    for x in (f, m, f400, f250, f900):
        try:
            x.close()
        except Exception:
            pass
    return info
