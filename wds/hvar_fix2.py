"""HVAR advance-delta rebuild after Latin merge.

BUG (found by doc-sync teammate, confirmed by measurement here):
  After P6 replaced hmtx base advances with Mona values, HVAR still carried
  Noto's advance deltas. Verified glyph by glyph: final and Noto HVAR Item
  arrays are IDENTICAL for H/T/o/x/a/n/A/V/W/Y (10/10 same).
  So real advance = Mona_base + Noto_delta, which is neither.
    H: 684 + 46 = 730, should be ~700  (+30 wrong)
    T: 576 + 41 = 617, should be ~572  (+45 wrong)

FIX: rebuild HVAR advance deltas by sampling Mona at 250/900, scaled,
minus the Mona base at 400, scaled. Only for glyphs we actually merged.

Also fixes the earlier failed attempt in hvar_fix.py: that module assumed
AdvWidthMap was a dict, but this font uses None (implicit glyph-id mapping),
so the whole loop was a no-op.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer


def rebuild_hvar(font_path, mona_path, merged_cps, out_path, sx):
    f = TTFont(font_path)
    hvar = f["HVAR"].table
    store = hvar.VarStore
    vd = store.VarData[0]
    regions = store.VarRegionList.Region

    idx_hi = idx_lo = None
    for i, ri in enumerate(vd.VarRegionIndex):
        ra = regions[ri].VarRegionAxis[0]
        if ra.PeakCoord > 0.5:
            idx_hi = i
        elif ra.PeakCoord < -0.5:
            idx_lo = i

    def adv_at(w):
        g = instancer.instantiateVariableFont(
            TTFont(mona_path), {"wght": w, "wdth": 100, "opsz": 0},
            inplace=True, updateFontNames=False, optimize=False)
        hm = g["hmtx"]
        d = {nm: hm[nm][0] for nm in g.getGlyphOrder()}
        g.close()
        return d

    a400, a250, a900 = adv_at(400), adv_at(250), adv_at(900)

    m = TTFont(mona_path)
    mcm = m.getBestCmap()
    ncm = f.getBestCmap()

    fixed = 0
    missed = []
    for cp in merged_cps:
        mname = mcm.get(cp)
        fname = ncm.get(cp)
        if mname is None or fname is None:
            continue
        if mname not in a400 or mname not in a250 or mname not in a900:
            missed.append((cp, fname))
            continue
        gi = f.getGlyphID(fname)
        base = f["hmtx"][fname][0]
        d_hi = int(round(a900[mname] * sx)) - base
        d_lo = int(round(a250[mname] * sx)) - base
        item = vd.Item[gi]
        if isinstance(item, list):
            item[idx_hi] = d_hi
            item[idx_lo] = d_lo
        else:
            vd.Item[gi] = [d_hi, d_lo] if idx_hi < idx_lo else [d_lo, d_hi]
        fixed += 1

    f.save(out_path)
    info = {"fixed": fixed, "missed": len(missed), "idx_hi": idx_hi,
            "idx_lo": idx_lo, "sample_missed": missed[:5]}
    f.close()
    m.close()
    return info
