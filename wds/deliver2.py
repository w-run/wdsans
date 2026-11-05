"""Static-instance builder that respects HVAR advances.

BUG: deliver.build_static uses instancer.instantiateVariableFont, which applies
gvar but NOT HVAR.  The variable font stores advance variation in HVAR (gvar
phantom points are all zero by design, matching the Noto base convention), so
every static instance came out with the DEFAULT advance:
    measured: H advance = 696 in all seven weights (should be 690/696/704/712)

FIX: after instantiating, overwrite each glyph's advance with the true value
measured from the variable font by harfbuzz at that weight.

Only touches advance widths - outlines come from the correct instancer output.
"""
from __future__ import annotations

import os
import subprocess

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from .rename import STOPS, FAMILY, PS_PREFIX, VENDOR, VERSION
from . import meta_fix

RIBBI = {"Regular", "Bold"}


def hb_advances(vf_path, wght, cps):
    """{cp: advance} measured from the VF at this weight (HVAR applied)."""
    out = {}
    batch = 500
    cl = [c for c in cps if c not in (0x20, 0xA0)]
    for i in range(0, len(cl), batch):
        chunk = cl[i:i + batch]
        chars = "".join(chr(c) for c in chunk)
        r = subprocess.run(
            ["hb-shape", f"--font-file={vf_path}",
             f"--variations=wght={wght}", chars],
            capture_output=True, text=True, check=True)
        segs = [s for s in r.stdout.strip().strip("[]").split("|") if "+" in s]
        if len(segs) != len(chunk):
            # fall back to per-character for this batch
            for cp in chunk:
                rr = subprocess.run(
                    ["hb-shape", f"--font-file={vf_path}",
                     f"--variations=wght={wght}", chr(cp)],
                    capture_output=True, text=True, check=True)
                ss = [s for s in rr.stdout.strip().strip("[]").split("|") if "+" in s]
                if len(ss) == 1:
                    out[cp] = int(ss[0].split("+")[1])
            continue
        for cp, s in zip(chunk, segs):
            out[cp] = int(s.split("+")[1])
    return out


def set_names(f, style, wght):
    nt = f["name"]
    is_ribbi = style in RIBBI
    family_1 = FAMILY if is_ribbi else f"{FAMILY} {style}"
    subfamily_2 = "Bold" if style == "Bold" else "Regular"
    ps = f"{PS_PREFIX}-{style}"

    def _s(nid, val):
        for pid, eid, lid in ((3, 1, 1033), (3, 1, 2052), (1, 0, 0)):
            nt.setName(val, nid, pid, eid, lid)

    _s(1, family_1)
    _s(2, subfamily_2)
    _s(4, FAMILY if is_ribbi else f"{family_1} {subfamily_2}")
    _s(6, ps)
    _s(16, FAMILY)
    _s(17, style)
    _s(3, f"{VERSION};{VENDOR};{ps};{VENDOR}")
    _s(5, VERSION)
    f["OS/2"].usWeightClass = wght
    f["head"].macStyle = 0x1 if style == "Bold" else 0x0


def build(vf_path, out_dir, woff2=True):
    os.makedirs(out_dir, exist_ok=True)
    vf = TTFont(vf_path)
    cps = [c for c in vf.getBestCmap()]
    vf.close()

    results = []
    for wght, style in STOPS:
        f = TTFont(vf_path)
        inst = instancer.instantiateVariableFont(
            f, {"wght": wght}, inplace=True,
            updateFontNames=False, optimize=False)
        for tbl in ("fvar", "gvar", "avar", "STAT", "HVAR"):
            if tbl in inst:
                del inst[tbl]

        # rewrite advances from harfbuzz truth
        adv = hb_advances(vf_path, wght, cps)
        cm = inst.getBestCmap()
        hmtx = inst["hmtx"]
        n = 0
        for cp, a in adv.items():
            g = cm.get(cp)
            if g is None:
                continue
            hmtx[g] = (a, hmtx[g][1])
            n += 1

        set_names(inst, style, wght)
        # fontbakery findings (P12)
        meta_fix.fix_version(inst)
        meta_fix.fix_fsselection(inst, style)
        inst["name"].names = [n for n in inst["name"].names if n.platformID != 1]
        p = os.path.join(out_dir, f"{PS_PREFIX}-{style}.ttf")
        inst.save(p)
        inst.close()
        results.append((p, os.path.getsize(p), n))

        if woff2:
            try:
                g = TTFont(p)
                g.flavor = "woff2"
                wp = p.replace(".ttf", ".woff2")
                g.save(wp)
                g.close()
                results.append((wp, os.path.getsize(wp), n))
            except Exception:
                results.append((p.replace(".ttf", ".woff2"), -1, n))
    return results
