"""基座加载与轴重设。

基座 = Noto Sans CJK SC VF（原生 TrueType glyf+gvar）。
其 fvar 默认字重是 100，而我们要 400 —— 用 (min, default, max) 三元组重设。
"""
from __future__ import annotations
import os
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

from . import paths

# 基座路径统一由 wds.paths 提供（P72），可用环境变量 WDSANS_ROOT 覆盖
SRC = paths.NOTO_VF

# 七档命名实例（wght 值 → 名称），DESIGN.md §3.3
STOPS = [
    (250, "Thin"),
    (300, "Light"),
    (350, "Normal"),
    (400, "Regular"),
    (500, "Medium"),
    (700, "Bold"),
    (900, "Heavy"),
]
AXIS_MIN, AXIS_DEF, AXIS_MAX = 250, 400, 900


def load_raw(path: str = SRC) -> TTFont:
    return TTFont(path)


def rebase_axis(font: TTFont, lo: int = AXIS_MIN, df: int = AXIS_DEF, hi: int = AXIS_MAX) -> TTFont:
    """把 wght 轴重设为 (lo, df, hi)。默认实例变为 df。"""
    return instancer.instantiateVariableFont(
        font, {"wght": (lo, df, hi)}, inplace=True, updateFontNames=False, optimize=False
    )


def instance_at(path_or_font, wght: int) -> TTFont:
    """取静态实例（用于测量 / 角色识别 / 出静态档）。"""
    f = TTFont(path_or_font) if isinstance(path_or_font, str) else path_or_font
    return instancer.instantiateVariableFont(
        f, {"wght": wght}, inplace=True, updateFontNames=False, optimize=False
    )


def glyph_point_counts(font: TTFont) -> dict:
    """glyf 里每个字形的真实点数（不含 phantom 点）。"""
    glyf = font["glyf"]
    out = {}
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0:
            out[name] = 0
        elif g.numberOfContours > 0:
            out[name] = len(g.coordinates)
        else:
            out[name] = -1  # 复合字形
    return out
