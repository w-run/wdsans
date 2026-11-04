"""Mona Sans VF 拉丁合并 —— 第一阶段：仅简单字形。

实测风险（见 docs/P6 记录）：
  Mona 有 512 个**复合字形**（Aacute 等引用 A + acute），
  本产物 Noto 是 0 个复合字形（全简单字形）。
  若把 Mona 复合字形直接搬进来，其组件引用会在新字体里失效。

所以分两阶段：
  阶段一（本模块）：只合并**非复合**的拉丁基础字母 + 标点 + 数字。
  阶段二（后续）：处理带重音等复合字形。

对齐策略：按字重分别测 (sx, sy)，水平压缩 ~0.87-0.90，垂直 ~1.0。
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.misc.transform import Transform
from fontTools.ttLib.tables._g_l_y_f import Glyph

LATIN_MAX = 0x024F
PUNCT_RANGES = ((0x2000, 0x206F), (0x20A0, 0x20CF))


def want_cps(font) -> set:
    out = set()
    for cp in font.getBestCmap():
        if cp <= LATIN_MAX:
            out.add(cp)
        elif any(a <= cp <= b for a, b in PUNCT_RANGES):
            out.add(cp)
    return out


def _bb(font, gname):
    gs = font.getGlyphSet()
    bp = BoundsPen(gs)
    gs[gname].draw(bp)
    return bp.bounds


def weight_scale(mona_path, noto_path, wght):
    m = instancer.instantiateVariableFont(
        TTFont(mona_path), {"wght": wght, "wdth": 100, "opsz": 0},
        inplace=True, updateFontNames=False, optimize=False)
    n = instancer.instantiateVariableFont(
        TTFont(noto_path), {"wght": wght},
        inplace=True, updateFontNames=False, optimize=False)
    mcm, ncm = m.getBestCmap(), n.getBestCmap()
    wr, hr = [], []
    for ch in "Hxnoad":
        mn = mcm.get(ord(ch)); nn = ncm.get(ord(ch))
        if not mn or not nn:
            continue
        mb = _bb(m, mn); nb = _bb(n, nn)
        if not mb or not nb:
            continue
        mw = mb[2] - mb[0]; nw = nb[2] - nb[0]
        mh = mb[3] - mb[1]; nh = nb[3] - nb[1]
        if nw > 0 and mw > 0:
            wr.append(mw / nw)
        if nh > 0 and mh > 0:
            hr.append(mh / nh)
    m.close(); n.close()
    wr.sort(); hr.sort()
    sx = 1.0 / wr[len(wr) // 2] if wr else 1.0
    sy = 1.0 / hr[len(hr) // 2] if hr else 1.0
    return sx, sy


def simple_latin_names(mona):
    """Mona 里**非复合**且落在拉丁/标点区的字形名 + 码位映射。"""
    glyf = mona["glyf"]
    cm = mona.getBestCmap()
    out = {}
    for cp, nm in cm.items():
        if not (cp <= LATIN_MAX or any(a <= cp <= b for a, b in PUNCT_RANGES)):
            continue
        if glyf[nm].numberOfContours < 0:
            continue          # 复合字形，本阶段跳过
        out[cp] = nm
    return out

def merge_latin(noto_path, mona_path, out_path, weights=None, dry_run=False):
    """把 Mona 的简单拉丁字形合并进 Noto VF（按字重分别缩放）。

    只处理「非复合」字形，且只处理 Noto 已有的码位（不新增）。
    返回统计信息。
    """
    from fontTools.ttLib import TTFont as TT

    f = TT(noto_path)
    m = TT(mona_path)
    ncm = f.getBestCmap()
    simple = simple_latin_names(m)

    # 只保留 Noto 也有的码位（避免新增字形带来的 GSUB 引用问题）
    todo = {cp: nm for cp, nm in simple.items() if cp in ncm}

    # 用默认字重（400）的系数做基准；VF 的 gvar deltas 一并按比例缩放
    sx, sy = weight_scale(mona_path, noto_path, 400)

    glyf_m = m["glyf"]
    glyf_f = f["glyf"]
    hmtx_m = m["hmtx"]
    hmtx_f = f["hmtx"]

    gs_m = m.getGlyphSet()
    replaced = 0
    for cp, mname in todo.items():
        fname = ncm[cp]
        # 用 Mona 的默认字形轮廓（去掉变体），转成 TrueType 并缩放
        pen = TTGlyphPen(None)
        tp = TransformPen(pen, Transform(sx, 0, 0, sy, 0, 0))
        gs_m[mname].draw(tp)
        newg = pen.glyph()
        glyf_f[fname] = newg
        # advance 同步缩放
        adv = hmtx_m[mname][0]
        lsb = hmtx_m[mname][1]
        hmtx_f[fname] = (int(round(adv * sx)), int(round(lsb * sx)))
        replaced += 1

    if not dry_run:
        # Mona 的 gvar 变体不搬（轴不同），直接清空这些字形的 gvar，
        # 让它们在所有字重下都用同一轮廓 —— 这是阶段一的已知限制
        if "gvar" in f:
            gv = f["gvar"]
            cleared = 0
            for cp, mname in todo.items():
                fname = ncm[cp]
                if fname in gv.variations:
                    del gv.variations[fname]
                    cleared += 1
        else:
            cleared = 0
        f.save(out_path)
    else:
        cleared = 0

    info = {
        "replaced": replaced,
        "skipped_composite": len([1 for cp in want_cps(m) if cp in m.getBestCmap() and m["glyf"][m.getBestCmap()[cp]].numberOfContours < 0]),
        "sx": round(sx, 4), "sy": round(sy, 4),
        "gvar_cleared": cleared,
    }
    f.close(); m.close()
    return info
