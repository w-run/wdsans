"""L1 全局仿射算子。

纯仿射 → 数学上不可能自交，也不可能改变点数。
"""
from __future__ import annotations

CX, CY = 500.0, 500.0  # 字面中心（UPM 1000）


def scale_about_center(contours, sx: float = 1.0, sy: float | None = None, cx=CX, cy=CY):
    """以字面中心为原点缩放。不改变笔画粗细比例（那是 stroke 的事）。"""
    if sy is None:
        sy = sx
    out = []
    for c in contours:
        out.append([_P(p.x, p.y, p.on, (p.x - cx) * sx + cx, (p.y - cy) * sy + cy) for p in c])
    return out


def translate(contours, dx: float = 0.0, dy: float = 0.0):
    out = []
    for c in contours:
        out.append([_P(p.x, p.y, p.on, p.x + dx, p.y + dy) for p in c])
    return out


class _P:
    __slots__ = ("x", "y", "on", "nx", "ny")

    def __init__(self, x, y, on, nx, ny):
        self.x, self.y, self.on = x, y, on
        self.nx, self.ny = nx, ny

    def __repr__(self):
        return f"({self.x:g},{self.y:g}->{self.nx:g},{self.ny:g})"
