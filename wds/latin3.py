"""Latin merge v3: replace base outline only, keep original gvar."""
from __future__ import annotations
from fontTools.ttLib import TTFont
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

LATIN_MAX = 0x024F
PUNCT_RANGES = ((0x2000, 0x206F), (0x20A0, 0x20CF))


def simple_latin_map(mona):
    glyf = mona["glyf"]
    cm = mona.getBestCmap()
    out = {}
    for cp, nm in cm.items():
        if not (cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT_RANGES)):
            continue
        if glyf[nm].numberOfContours < 0:
            continue
        out[cp] = nm
    return out


def merge_base_only(noto_path, mona_path, out_path, sx, sy):
    f = TTFont(noto_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    smap = simple_latin_map(m)
    todo = {cp: nm for cp, nm in smap.items() if cp in ncm}

    gs_m = m.getGlyphSet()
    glyf_f = f["glyf"]
    hmtx_m = m["hmtx"]
    hmtx_f = f["hmtx"]

    replaced = 0
    mismatched = []
    for cp, mname in todo.items():
        fname = ncm[cp]
        pen = TTGlyphPen(None)
        tp = TransformPen(pen, Transform(sx, 0, 0, sy, 0, 0))
        gs_m[mname].draw(tp)
        newg = pen.glyph()
        old = glyf_f[fname]
        if old.numberOfContours > 0 and newg.numberOfContours > 0:
            if len(old.coordinates) != len(newg.coordinates):
                mismatched.append((fname, len(old.coordinates), len(newg.coordinates)))
                continue
        glyf_f[fname] = newg
        adv, lsb = hmtx_m[mname]
        hmtx_f[fname] = (int(round(adv * sx)), int(round(lsb * sx)))
        replaced += 1

    f.save(out_path)
    info = {"replaced": replaced, "mismatched": len(mismatched),
            "sample": mismatched[:6], "sx": round(sx,4), "sy": round(sy,4)}
    f.close()
    m.close()
    return info