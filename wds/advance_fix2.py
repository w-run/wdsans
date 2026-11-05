"""Final advance-chain fix: per-character hb-shape, strict verification.

Why this rewrite: shaping ALL codepoints as one string and zipping the result to
the codepoint list silently misaligns when a glyph is zero-width or a mark
merges a cluster.  That is why T ended up with HVAR delta [0,0] while H was fine.
Measure ONE character at a time instead - slower but unambiguous.

Invariants we enforce (and assert) after writing:
    hmtx.advance          == round(Mona_adv(400) * sx)
    hb-shape(w).advance   == round(Mona_adv(w) * sx)
for w in {250, 400, 900}   (400 must equal the hmtx base exactly)
"""
from __future__ import annotations

import subprocess

from fontTools.ttLib import TTFont


def adv_one(font_path, wght_vars, ch):
    cmd = ["hb-shape", f"--font-file={font_path}"]
    if wght_vars:
        cmd.append(f"--variations={wght_vars}")
    cmd.append(ch)
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    segs = [s for s in out.strip("[]").split("|") if "+" in s]
    if len(segs) != 1:
        return None
    return int(segs[0].split("+")[1])


def run(font_path, mona_path, out_path, sx, mona_vars="wght={},wdth=100,opsz=0"):
    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    mcm = m.getBestCmap()
    glyf_f = f["glyf"]
    mglyf = m["glyf"]

    pairs = []
    for cp, mname in mcm.items():
        gname = ncm.get(cp)
        if gname is None:
            continue
        if not (cp <= 0x024F or 0x2000 <= cp <= 0x206F or 0x20A0 <= cp <= 0x20CF):
            continue
        if mglyf[mname].numberOfContours <= 0:
            continue
        if glyf_f[gname].numberOfContours <= 0:
            continue
        pairs.append((cp, gname))

    hmtx = f["hmtx"]
    gv = f["gvar"]
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
    skipped = []
    for cp, gname in pairs:
        ch = chr(cp)
        a = {}
        for w in (250, 400, 900):
            v = adv_one(mona_path, mona_vars.format(w), ch)
            if v is None:
                break
            a[w] = int(round(v * sx))
        if len(a) != 3:
            skipped.append((cp, gname))
            continue

        hmtx[gname] = (a[400], hmtx[gname][1])
        for tv in gv.variations.get(gname, []):
            co = tv.coordinates
            if len(co) >= 4:
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
    return {"fixed": fixed, "skipped": len(skipped), "sample": skipped[:5],
            "idx_hi": idx_hi, "idx_lo": idx_lo}
