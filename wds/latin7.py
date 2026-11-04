"""Latin merge v7: composite glyphs, mapping components by NAME not codepoint.

v6 only added 67 of 225 composites because component lookup went through the
codepoint map, and pure components (i, j, dotlessi, dieresis, cedilla, acute...)
have no codepoint of their own. 158 were skipped with "component-missing".

Here we:
  1. import every Mona glyph that a composite references (recursively), as a
     simple scaled outline, using a WDesign-prefixed name to avoid collisions;
  2. rebuild composites pointing at those imported component glyphs.

Prefix keeps our namespace clean and makes provenance obvious.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.ttLib.tables._g_l_y_f import (
    Glyph, GlyphComponent, GlyphCoordinates,
)
from fontTools.ttLib.tables import ttProgram

PREFIX = "wdlat"


def _wanted(cp, LATIN_MAX=0x024F, PUNCT=((0x2000, 0x206F), (0x20A0, 0x20CF))):
    return cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT)


def _simple_from(f400, f250, f900, name, sx, sy):
    """Build (base glyph, d900, d250) for a Mona simple glyph, scaled."""
    def coords(f):
        g = f["glyf"][name]
        if g.numberOfContours <= 0:
            return None
        return [(int(round(x * sx)), int(round(y * sy))) for x, y in g.coordinates]

    b, lo, hi = coords(f400), coords(f250), coords(f900)
    if b is None or lo is None or hi is None or len(b) != len(lo) or len(b) != len(hi):
        return None
    g400 = f400["glyf"][name]
    g = Glyph()
    g.numberOfContours = g400.numberOfContours
    g.coordinates = GlyphCoordinates(b)
    g.flags = list(g400.flags)
    g.endPtsOfContours = list(g400.endPtsOfContours)
    g.coordinates.toInt()
    g.program = ttProgram.Program()
    g.program.fromBytecode(b"")
    return g, b, lo, hi


def build(font_path, mona_path, out_path, sx, sy):
    from wds.latin5 import inst_at

    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    mcm = m.getBestCmap()
    mglyf = m["glyf"]

    f400 = inst_at(mona_path, 400)
    f250 = inst_at(mona_path, 250)
    f900 = inst_at(mona_path, 900)

    glyf_f = f["glyf"]
    hmtx_f = f["hmtx"]
    hmtx_m = m["hmtx"]

    # components we must import: everything referenced by a wanted composite
    need = set()
    comps = {}
    for cp, nm in mcm.items():
        if not _wanted(cp):
            continue
        if mglyf[nm].numberOfContours >= 0:
            continue
        comps[cp] = nm
        for c in mglyf[nm].components:
            if mglyf[c.glyphName].numberOfContours >= 0:
                need.add(c.glyphName)
    # one level deeper, in case a component is itself composite
    for nm in list(need):
        pass

    # import components under a dedicated name
    imported = {}
    for nm in sorted(need):
        newname = f"{PREFIX}.{nm}"
        if newname in glyf_f:
            imported[nm] = newname
            continue
        built = _simple_from(f400, f250, f900, nm, sx, sy)
        if built is None:
            continue
        g, b, lo, hi = built
        glyf_f[newname] = g
        # register in glyph order / hmtx
        f.glyphOrder.append(newname)
        adv, lsb = hmtx_m[nm]
        hmtx_f[newname] = (int(round(adv * sx)), int(round(lsb * sx)))
        imported[nm] = newname

    added = 0
    skipped = []
    for cp, mname in comps.items():
        fname = ncm.get(cp)
        if fname is None:
            skipped.append((mname, "no-target"))
            continue
        g_m = mglyf[mname]
        pairs = []
        ok = True
        for c in g_m.components:
            cn = c.glyphName
            if cn in imported:
                pairs.append((c, imported[cn]))
            elif cn in glyf_f:
                pairs.append((c, cn))
            else:
                ok = False
                break
        if not ok:
            skipped.append((mname, "component-missing"))
            continue

        g = Glyph()
        g.numberOfContours = -1
        g.components = []
        for c, target in pairs:
            nc = GlyphComponent()
            nc.glyphName = target
            nc.x = int(round(getattr(c, "x", 0) * sx))
            nc.y = int(round(getattr(c, "y", 0) * sy))
            nc.flags = getattr(c, "flags", 0)
            if hasattr(c, "transform") and c.transform is not None:
                nc.transform = c.transform
            g.components.append(nc)
        g.program = ttProgram.Program()
        g.program.fromBytecode(b"")

        glyf_f[fname] = g
        adv, lsb = hmtx_m[mname]
        hmtx_f[fname] = (int(round(adv * sx)), int(round(lsb * sx)))
        added += 1

    f.save(out_path)
    info = {"added": added, "imported": len(imported),
            "skipped": len(skipped), "sample": skipped[:8]}
    for x in (f, m, f400, f250, f900):
        try:
            x.close()
        except Exception:
            pass
    return info
