"""Fix HVAR after Latin merge: advance deltas must follow Mona.

Bug found by measurement: after replacing hmtx base advance with Mona values,
HVAR still carried Noto deltas -> advance frozen (H adv = 675 at both 250 and 900).

Fix: rebuild the HVAR advance deltas for merged glyphs, sampling Mona at 250/900.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.varLib.models import piecewiseLinearMap


def rebuild_hvar(font, mona_path, merged_map, sx):
    """merged_map: {glyphname_in_ours: mona_glyphname}."""
    if "HVAR" not in font:
        return 0
    hvar = font["HVAR"].table
    adv_map = hvar.AdvWidthMap
    if adv_map is None:
        return 0

    store = hvar.VarStore
    regions = store.VarRegionList.Region
    # find region index for wght peak +1 and -1 (2 regions measured)
    def region_peak(r):
        for ax, (s, p, e) in r.VarRegionAxis[0].__dict__.items():
            pass
        ra = r.VarRegionAxis[0]
        return (ra.StartCoord, ra.PeakCoord, ra.EndCoord)

    idx_hi = idx_lo = None
    for i, r in enumerate(regions):
        sc, pc, ec = region_peak(r)
        if pc > 0.5:
            idx_hi = i
        elif pc < -0.5:
            idx_lo = i

    def adv_at(w):
        f = instancer.instantiateVariableFont(
            TTFont(mona_path), {"wght": w, "wdth": 100, "opsz": 0},
            inplace=True, updateFontNames=False, optimize=False)
        hm = f["hmtx"]
        d = {nm: hm[nm][0] for nm in f.getGlyphOrder()}
        f.close()
        return d

    a400 = adv_at(400)
    a250 = adv_at(250)
    a900 = adv_at(900)

    n = 0
    for ours, mona_nm in merged_map.items():
        if mona_nm not in a400 or mona_nm not in a250 or mona_nm not in a900:
            continue
        base = int(round(a400[mona_nm] * sx))
        d_hi = int(round(a900[mona_nm] * sx)) - base
        d_lo = int(round(a250[mona_nm] * sx)) - base
        try:
            varidx = adv_map.mapping[ours]
        except Exception:
            continue
        if varidx >= len(store.VarData):
            continue
        vd = store.VarData[varidx]
        if idx_hi is not None and idx_hi < len(vd.VarRegionIndex):
            vd.Item[idx_hi] = [d_hi]
        if idx_lo is not None and idx_lo < len(vd.VarRegionIndex):
            vd.Item[idx_lo] = [d_lo]
        vd.Item = [[v] if not isinstance(v, list) else v for v in vd.Item]
        n += 1
    return n