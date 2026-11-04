"""Latin merge v6: also bring Mona's composite (accented) glyphs.

Problem measured in v5 output:
  A (Mona) width 569 vs Aacute (Noto) width 594  -> +4.4%
  o (Mona) width 436 vs odieresis (Noto) width 488 -> +12%
i.e. plain letters came from Mona, accented variants stayed Noto, so the
same letter looked different with and without an accent. Visible inconsistency.

Solution: for composite glyphs in Mona's Latin range, rebuild them as TrueType
composites referencing the ALREADY-MERGED base glyph and a merged accent glyph.

Noto has zero composites, so we must create the composite structure ourselves:
  Glyph(numberOfContours=-1) with .components = [GlyphComponent(glyphName, ...)]
The components must point at glyph names that exist in our font, so we map
Mona's component names to our glyph names via the codepoint map.
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent, GlyphCoordinates
from fontTools.ttLib.tables import ttProgram


def _wanted(cp, LATIN_MAX=0x024F, PUNCT=((0x2000, 0x206F), (0x20A0, 0x20CF))):
    return cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT)


def composite_map(mona, LATIN_MAX=0x024F,
                  PUNCT=((0x2000, 0x206F), (0x20A0, 0x20CF))):
    glyf = mona["glyf"]
    cm = mona.getBestCmap()
    out = {}
    for cp, nm in cm.items():
        if not _wanted(cp, LATIN_MAX, PUNCT):
            continue
        if glyf[nm].numberOfContours < 0:
            out[cp] = nm
    return out


def build(font_path, mona_path, out_path, sx, sy):
    """Add Mona's composite Latin glyphs to an already-merged font."""
    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    mcm = m.getBestCmap()
    mglyf = m["glyf"]

    # our glyph name for a Mona glyph name (via codepoint)
    cp_of_mona_name = {}
    for cp, nm in mcm.items():
        cp_of_mona_name.setdefault(nm, cp)

    def our_name_for(mona_name):
        cp = cp_of_mona_name.get(mona_name)
        if cp is None:
            return None
        return ncm.get(cp)

    comps = composite_map(m)
    glyf_f = f["glyf"]
    hmtx_m = m["hmtx"]
    hmtx_f = f["hmtx"]

    added = 0
    skipped = []
    for cp, mname in comps.items():
        fname = ncm.get(cp)
        if fname is None:
            skipped.append((mname, "no-target"))
            continue
        g_m = mglyf[mname]
        newc = []
        ok = True
        for c in g_m.components:
            target = our_name_for(c.glyphName)
            if target is None or target not in glyf_f:
                ok = False
                break
            newc.append((c, target))
        if not ok:
            skipped.append((mname, "component-missing"))
            continue

        g = Glyph()
        g.numberOfContours = -1
        g.components = []
        for c, target in newc:
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
    info = {"added": added, "skipped": len(skipped), "sample": skipped[:8]}
    f.close(); m.close()
    return info
