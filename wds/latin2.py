"""拉丁合并 —— 修正版：自己构造 gvar deltas。

前版错误：清空 gvar -> 拉丁所有字重同粗细（实测 H高 250/400/700 全 732）。

本版做法：
  对每个拉丁字形，从 Mona 在 250 / 400 / 900 三个字重处取轮廓（缩放后），
  base 用 400，然后按我方 gvar 的 tuple 结构填 delta。
  这样拉丁的粗细随字重正常变化。

关键前提：三处取值必须来自 Mona 的**同一字形**，点数/顺序天然一致。
"""
from __future__ import annotations

from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools.pens.recordingPen import RecordingPen


def outline_at(mona_path, wght, sx, sy):
    """返回 {glyphname: [(x,y), ...]} —— Mona 在该字重、缩放后的 on/off 点序列。"""
    f = instancer.instantiateVariableFont(
        TTFont(mona_path), {"wght": wght, "wdth": 100, "opsz": 0},
        inplace=True, updateFontNames=False, optimize=False)
    glyf = f["glyf"]
    out = {}
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        coords = [(round(x * sx), round(y * sy)) for x, y in g.coordinates]
        out[name] = coords
    f.close()
    return out


def contours_of(font, name):
    """返回字形各轮廓的 (coords, endpts, flags)。"""
    g = font["glyf"][name]
    coords = list(g.coordinates)
    flags = list(g.flags)
    ends = list(g.endPtsOfContours)
    return coords, ends, flags
