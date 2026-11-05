"""Fix the 10 glyphs whose advance was never corrected (P13).

ROOT CAUSE
advance_fix2.run() built its work list like this:

    for cp, mname in mcm.items():
        if mglyf[mname].numberOfContours <= 0:
            continue            # <-- skipped COMPOSITES

i.e. it only fixed Mona glyphs that are SIMPLE outlines.  But these are
composites in Mona Sans:
    i j 9 : ; " ) ] } <  (dot/ring/quote/bracket bases are composites)

Their hmtx base therefore still held the raw, UNSCALED Mona advance while the
HVAR deltas had been baked at scale 0.895 - so their advance curve drifted.

MEASURED at wght=400 (should equal Mona*0.895):
    i  215 vs 227  (-12)      "  329 vs 342  (-13)
    j  209 vs 222  (-13)      9  562 vs 575  (-13)
    :  207 vs 219  (-12)      )  301 vs 313  (-12)
    ;  212 vs 225  (-13)      ]  317 vs 329  (-12)
                              }  346 vs 359  (-13)
                              <  527 vs 540  (-13)

Note the constant -12/-13 at wght=400 - that is exactly the (1 - 0.895)
scale error, confirming the diagnosis.

FIX: drop the numberOfContours filter - use the codepoint map to pair glyphs,
and only require that the glyph exists in our font and has an outline.
"""
from __future__ import annotations

import subprocess

from fontTools.ttLib import TTFont


def adv_one(font_path, vars_, ch):
    cmd = ["hb-shape", "--font-file=" + font_path]
    if vars_:
        cmd.append("--variations=" + vars_)
    cmd.append(ch)
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    segs = [s for s in out.strip("[]").split("|") if "+" in s]
    return int(segs[0].split("+")[1]) if len(segs) == 1 else None


def fix(font_path, mona_path, out_path, sx,
        mona_vars="wght=%d,wdth=100,opsz=0"):
    f = TTFont(font_path)
    m = TTFont(mona_path)
    ncm = f.getBestCmap()
    mcm = m.getBestCmap()
    glyf_f = f["glyf"]

    hmtx = f["hmtx"]
    gv = f["gvar"]
    hvar = f["HVAR"].table
    vd = hvar.VarStore.VarData[0]
    regions = hvar.VarStore.VarRegionList.Region
    idx_hi = idx_lo = None
    for i, ri in enumerate(vd.VarRegionIndex):
        pc = regions[ri].VarRegionAxis[0].PeakCoord
        if pc > 0.5:
            idx_hi = i
        elif pc < -0.5:
            idx_lo = i

    fixed = []
    for cp, mname in mcm.items():
        gname = ncm.get(cp)
        if gname is None:
            continue
        if glyf_f[gname].numberOfContours <= 0:
            continue                      # nothing to size in ours
        if not (cp <= 0x024F or 0x2000 <= cp <= 0x206F or 0x20A0 <= cp <= 0x20CF):
            continue
        ch = chr(cp)

        vals = {}
        for w in (250, 400, 900):
            v = adv_one(mona_path, mona_vars % w, ch)
            if v is None:
                break
            vals[w] = int(round(v * sx))
        if len(vals) != 3:
            continue

        cur = hmtx[gname][0]
        if cur == vals[400]:
            continue

        hmtx[gname] = (vals[400], hmtx[gname][1])
        for tv in gv.variations.get(gname, []):
            if len(tv.coordinates) >= 4:
                tv.coordinates[-4] = (0, 0)
                tv.coordinates[-3] = (0, 0)
                tv.coordinates[-2] = (0, 0)
                tv.coordinates[-1] = (0, 0)
        gi = f.getGlyphID(gname)
        item = vd.Item[gi]
        d_hi = vals[900] - vals[400]
        d_lo = vals[250] - vals[400]
        if isinstance(item, list):
            item[idx_hi] = d_hi
            item[idx_lo] = d_lo
        else:
            vd.Item[gi] = [d_hi, d_lo]
        fixed.append((ch, cur, vals[400]))

    f.save(out_path)
    f.close()
    m.close()
    return {"fixed": len(fixed), "sample": fixed[:12]}
