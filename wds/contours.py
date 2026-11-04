"""轮廓读取：把字形拆成 on/off 点序列，供算子使用。

关键：点的顺序必须与 glyf.coordinates 完全一致，否则改写 gvar 会错位。
drawPoints 给出的顺序 == glyf 点序（已验证）。
"""
from __future__ import annotations


class _Collect:
    __slots__ = ("contours", "cur")

    def __init__(self):
        self.contours = []
        self.cur = None

    def beginPath(self, identifier=None, **kw):
        self.cur = []

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kw):
        self.cur.append(_P(float(pt[0]), float(pt[1]), segmentType is not None))

    def endPath(self):
        self.contours.append(self.cur)
        self.cur = None

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kw):
        raise NotImplementedError("复合字形暂不支持（需先展开）")


class _P:
    __slots__ = ("x", "y", "on")

    def __init__(self, x, y, on):
        self.x = x
        self.y = y
        self.on = on

    def __repr__(self):
        return f"({self.x:g},{self.y:g}{'' if self.on else 'o'})"


def read_points(glyph_set, name: str):
    pen = _Collect()
    glyph_set[name].drawPoints(pen)
    return pen.contours


def flatten(contours):
    return [p for c in contours for p in c]
