"""Latin merge v4: rebuild gvar deltas by sampling Mona."""
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


def inst_at(mona_path, wght, sx, sy):
    return instancer.instantiateVariableFont(
        TTFont(mona_path), {"wght": wght, "wdth": 100, "opsz": 0},
        inplace=True, updateFontNames=False, optimize=False)


def coords_at(f, name, sx, sy):
    g = f["glyf"][name]
    if g.numberOfContours <= 0:
        return None
    return [(int(round(x * sx)), int(round(y * sy))) for x, y in g.coordinates]


def merge(noto_path, mona_path, out_path, sx, sy):
    f = TTFont(noto_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    smap = simple_latin_map(m)
    todo = {cp: nm for cp, nm in smap.items() if cp in ncm}
    hmtx_m = m["hmtx"]

    f400 = inst_at(mona_path, 400, sx, sy)
    f250 = inst_at(mona_path, 250, sx, sy)
    f900 = inst_at(mona_path, 900, sx, sy)

    glyf_f = f["glyf"]
    gv = f["gvar"]
    hmtx_f = f["hmtx"]

    replaced = 0
    skipped = []
    for cp, mname in todo.items():
        b = coords_at(f400, mname, 1.0, 1.0)
        lo = coords_at(f250, mname, 1.0, 1.0)
        hi = coords_at(f900, mname, 1.0, 1.0)
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
        adv, lsb = hmtx_m[mname]
        hmtx_f[fname] = (int(round(adv * sx)), int(round(lsb * sx)))

        n = len(b)
        d900 = [(hi[i][0] - b[i][0], hi[i][1] - b[i][1]) for i in range(n)] + [(0, 0)] * 4
        d250 = [(lo[i][0] - b[i][0], lo[i][1] - b[i][1]) for i in range(n)] + [(0, 0)] * 4
        t_hi = TupleVariation({"wght": (0.0, 1.0, 1.0)}, d900)
        t_lo = TupleVariation({"wght": (-1.0, -1.0, 0.0)}, d250)
        gv.variations[fname] = [t_hi, t_lo]
        replaced += 1

    f.save(out_path)
    info = {"replaced": replaced, "skipped": len(skipped), "skip_sample": skipped[:6]}
    f.close()
    return info