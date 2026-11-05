"""Advance-chain repair: hmtx base + gvar phantom + HVAR, all consistent.

Root causes found by measurement (three separate bugs, all mine):
 1. Mona Sans's default weight is wght=200; ours is 400.  latin5 read hmtx from
    Mona's DEFAULT instance, so every base advance was the 200-level width.
    (T base came out 576 where the 400 level is ~489.)
 2. instancer.instantiateVariableFont does NOT apply HVAR.  Reading Mona's
    advance at 250/900 that way returns hmtx-only values:
        instancer H@900 = 782   vs   hb-shape H@900 = 796
    So HVAR deltas built from instancer data are wrong.
 3. HVAR still held Noto's advance deltas (verified: final and Noto Item arrays
    identical for H/T/o/x/a/n/A/V/W/Y), while hmtx base had become Mona's.

Correct tool split (this module):
    outlines / xMin  -> instancer   (gvar IS applied, HVAR is irrelevant)
    advances         -> hb-shape   (HVAR IS applied)

For each merged glyph we write:
    hmtx.advance      = A400
    hmtx.lsb          = xMin400                (so pp1 base == 0)
    gvar pp1.x delta  = xMinw - xMin400
    gvar pp2.x delta  = (xMinw - xMin400) + (Aw - A400)
    HVAR advance del  = Aw - A400
"""
from __future__ import annotations

import subprocess

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer


def shape_advances(font_path, cps, weights, variations):
    """{wght: {cp: advance}} via harfbuzz (HVAR applied)."""
    chars = "".join(chr(c) for c in cps)
    out = {}
    for w in weights:
        r = subprocess.run(
            ["hb-shape", f"--font-file={font_path}",
             f"--variations={variations.format(w)}", chars],
            capture_output=True, text=True, check=True)
        advs = [int(s.split("+")[1])
                for s in r.stdout.strip().strip("[]").split("|") if "+" in s]
        if len(advs) != len(cps):
            raise RuntimeError(f"{w}: got {len(advs)} advances for {len(cps)} cps")
        out[w] = dict(zip(cps, advs))
    return out


def xmin_at(font_path, variations_fmt, weights, mona_names):
    """{wght: {mona_name: xMin}} via instancer (gvar applied)."""
    out = {}
    for w in weights:
        f = instancer.instantiateVariableFont(
            TTFont(font_path), _coords(variations_fmt.format(w)),
            inplace=True, updateFontNames=False, optimize=False)
        glyf = f["glyf"]
        d = {}
        for nm in mona_names:
            g = glyf[nm]
            if g.numberOfContours > 0 and len(g.coordinates):
                d[nm] = min(int(round(x)) for x, _ in g.coordinates)
        out[w] = d
        f.close()
    return out


def _coords(v):
    d = {}
    for part in v.split(","):
        k, val = part.split("=")
        d[k] = float(val)
    return d


def run(font_path, mona_path, out_path, sx, mona_vars="wght={},wdth=100,opsz=0"):
    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()

    # codepoints we have a Mona glyph for, and that are simple glyphs in ours
    pairs = []           # (cp, our_glyph, mona_glyph)
    glyf_f = f["glyf"]
    for cp, mname in m.getBestCmap().items():
        gname = ncm.get(cp)
        if gname is None:
            continue
        if glyf_f[gname].numberOfContours <= 0:
            continue
        if m["glyf"][mname].numberOfContours <= 0:
            continue
        if not (cp <= 0x024F or 0x2000 <= cp <= 0x206F or 0x20A0 <= cp <= 0x20CF):
            continue
        pairs.append((cp, gname, mname))

    cps = [p[0] for p in pairs]
    mona_names = [p[2] for p in pairs]
    weights = (250, 400, 900)

    adv = shape_advances(mona_path, cps, weights, mona_vars)
    xm = xmin_at(mona_path, mona_vars, weights, mona_names)

    gv = f["gvar"]
    hmtx = f["hmtx"]
    hvar = f["HVAR"].table
    store = hvar.VarStore
    vd = store.VarData[0]
    regions = store.VarRegionList.Region
    idx_hi = idx_lo = None
    for i, ri in enumerate(vd.VarRegionIndex):
        pc = regions[ri].VarRegionAxis[0].PeakCoord
        if pc > 0.5:
            idx_hi = i
        elif pc < -0.5:
            idx_lo = i

    fixed = 0
    for cp, gname, mname in pairs:
        if any(cp not in adv[w] or mname not in xm[w] for w in weights):
            continue
        a = {w: int(round(adv[w][cp] * sx)) for w in weights}
        xs = {w: int(round(xm[w][mname] * sx)) for w in weights}

        hmtx[gname] = (a[400], xs[400])

        tvs = gv.variations.get(gname)
        if not tvs or len(tvs) < 2:
            continue
        for tv in tvs:
            peak = tv.axes["wght"][1]
            w = 900 if peak > 0 else 250
            co = tv.coordinates
            if len(co) < 4:
                continue
            # Convention measured in the Noto base: gvar phantom points are
            # ALL ZERO and the advance variation lives purely in HVAR.
            # Writing both double-counts (T froze at 592 in every weight).
            co[-4] = (0, 0)
            co[-3] = (0, 0)
            co[-2] = (0, 0)
            co[-1] = (0, 0)

        gi = f.getGlyphID(gname)
        item = vd.Item[gi]
        d_hi = a[900] - a[400]
        d_lo = a[250] - a[400]
        if isinstance(item, list):
            item[idx_hi] = d_hi
            item[idx_lo] = d_lo
        else:
            vd.Item[gi] = [d_hi, d_lo]
        fixed += 1

    f.save(out_path)
    f.close()
    m.close()
    return {"fixed": fixed, "pairs": len(pairs)}
