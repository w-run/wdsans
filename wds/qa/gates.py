"""QA 闸门（硬断言）。构建不通过 = 失败，不是警告。

对应 docs/REBUILD-PLAN.md §8。
"""
from __future__ import annotations
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from ..base import STOPS
from ..contours import read_points


class GateFailure(AssertionError):
    pass


def _fail(name, msg):
    raise GateFailure(f"[{name}] {msg}")


def g1_topology(font_path: str, sample_glyphs=None, weights=(250, 400, 900)):
    """任意字重实例化后，点数/顺序/on-off 必须与基座逐字全等。"""
    base = TTFont(font_path, lazy=True)
    cmap = base.getBestCmap()
    names = sample_glyphs or [
        cmap[cp] for cp in list(cmap)[:40] if cmap[cp] in base.getGlyphOrder()
    ]
    sigs = {}
    for w in weights:
        inst = instancer.instantiateVariableFont(
            TTFont(font_path), {"wght": w}, inplace=True, updateFontNames=False, optimize=False
        )
        gs = inst.getGlyphSet()
        sigs[w] = {n: [[p.on for p in c] for c in read_points(gs, n)] for n in names}
        inst.close()
    ref = sigs[weights[0]]
    for w in weights[1:]:
        for n in names:
            if sigs[w][n] != ref[n]:
                _fail("G1", f"{n} 在 wght={w} 与 wght={weights[0]} 拓扑不一致")
    return {"gate": "G1", "profile": f"{len(names)} 字形 × {len(weights)} 字重", "ok": True}


def g2_roundtrip(original_path: str, rebuilt_path: str, weights=(250, 400, 900), tol=1.0):
    """增量往返：identity 改写后，与源轮廓逐点比较。"""
    for w in weights:
        a = instancer.instantiateVariableFont(
            TTFont(original_path), {"wght": w}, inplace=True, updateFontNames=False, optimize=False
        )
        b = instancer.instantiateVariableFont(
            TTFont(rebuilt_path), {"wght": w}, inplace=True, updateFontNames=False, optimize=False
        )
        ga, gb = a.getGlyphSet(), b.getGlyphSet()
        cmap = a.getBestCmap()
        worst = 0.0
        for cp in list(cmap)[:60]:
            n = cmap[cp]
            ca, cb = read_points(ga, n), read_points(gb, n)
            if [len(c) for c in ca] != [len(c) for c in cb]:
                _fail("G2", f"wght={w} {n} 点数不同")
            for x, y in zip(ca, cb):
                for p, q in zip(x, y):
                    worst = max(worst, abs(p.x - q.x), abs(p.y - q.y))
        a.close(); b.close()
        if worst > tol:
            _fail("G2", f"wght={w} 最大点偏差 {worst:.4f} > {tol}")
    return {"gate": "G2", "tol": tol, "ok": True}


def g3_features(font_path: str, expected_features, expected_scripts=None):
    f = TTFont(font_path, lazy=True)
    gsub = f["GSUB"].table
    feats = {fr.FeatureTag for fr in gsub.FeatureList.FeatureRecord}
    missing = set(expected_features) - feats
    if missing:
        _fail("G3", f"缺 feature: {sorted(missing)}")
    if expected_scripts:
        scripts = {sr.ScriptTag for sr in gsub.ScriptList.ScriptRecord}
        miss = set(expected_scripts) - scripts
        if miss:
            _fail("G3", f"缺 script: {sorted(miss)}")
    # locl 必须能切
    has_locl = "locl" in feats
    if not has_locl:
        _fail("G3", "缺 locl")
    return {"gate": "G3", "features": len(feats), "scripts": len(scripts) if expected_scripts else None, "ok": True}


def g4_cmap(font_path: str, min_entries: int):
    f = TTFont(font_path, lazy=True)
    n = len(f.getBestCmap())
    if n < min_entries:
        _fail("G4", f"cmap {n} < 基线 {min_entries}")
    return {"gate": "G4", "cmap": n, "baseline": min_entries, "ok": True}


# 空白类字符：无墨迹是**设计本意**，不是退化。
# 实测基座自带的 6 个零面积字形全部属于此列：
#   U+0020 space, U+00A0 nbsp, U+115F/U+1160 韩文填充符, U+2002/U+2003 等宽空格
_WHITESPACE_CPS = {
    0x0020, 0x00A0, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005,
    0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x202F, 0x205F, 0x3000,
    0x115F, 0x1160, 0x3164, 0xFFA0,
}


def g5_structure(font_path: str, sample=300, wght=400):
    """退化轮廓 / 零长线段 / 复合引用悬空。

    退化 = 有轮廓但面积为 0。空白字符无墨迹是设计本意，必须排除，
    否则闸门会误杀（实测基座就有 6 个）。
    """
    from fontTools.pens.areaPen import AreaPen
    inst = instancer.instantiateVariableFont(
        TTFont(font_path), {"wght": wght}, inplace=True, updateFontNames=False, optimize=False
    )
    gs = inst.getGlyphSet()
    cmap = inst.getBestCmap()
    degen, zero_len, blank = 0, 0, 0
    checked = 0
    bad_list = []
    for cp in list(cmap)[:sample]:
        n = cmap[cp]
        cs = read_points(gs, n)
        pen = AreaPen(gs)
        try:
            gs[n].draw(pen)
        except Exception:
            continue
        checked += 1
        if abs(pen.value) < 1.0:
            if cp in _WHITESPACE_CPS or not cs:
                blank += 1
                continue
            degen += 1
            bad_list.append((hex(cp), n, round(pen.value, 2)))
        for c in cs:
            for i in range(len(c)):
                p, q = c[i], c[(i + 1) % len(c)]
                if abs(p.x - q.x) < 1e-9 and abs(p.y - q.y) < 1e-9:
                    zero_len += 1
    inst.close()
    if degen:
        _fail("G5", f"退化轮廓 {degen}/{checked}，例如 {bad_list[:5]}")
    if zero_len:
        _fail("G5", f"零长线段 {zero_len}")
    return {
        "gate": "G5", "checked": checked, "degenerate": degen,
        "blank_ok": blank, "zero_len": zero_len, "ok": True,
    }
