"""笔画几何测量 —— 取代基于 bbox 的粗估。

核心方法：**法向投射测厚**。
  对轮廓上的点，取其局部法向，向内投射射线，与其它轮廓边求最近交点 →
  该点处的真实笔画厚度。

这比 glow-sans 的 `maxStroke = hstroke * 1.5` 常数猜测可靠：
  - 不受字形整体尺寸影响（「口」与「齉」量出同量级笔画宽）
  - 每点独立测量，能反映笔画粗细变化
"""
from __future__ import annotations
import math


def _seg_intersect(p, d, a, b):
    """射线 p + t*d 与线段 a-b 的交点参数 t（>0 表示正向）。"""
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = d[0] * ey - d[1] * ex
    if abs(den) < 1e-12:
        return None
    t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
    u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
    if t > 1e-6 and -1e-9 <= u <= 1 + 1e-9:
        return t
    return None


def all_edges(contours):
    """所有轮廓的所有线段 [(a, b, contour_index)]。"""
    out = []
    for ci, c in enumerate(contours):
        n = len(c)
        for i in range(n):
            p, q = c[i], c[(i + 1) % n]
            out.append(((p.x, p.y), (q.x, q.y), ci))
    return out


def local_normal(c, i):
    """点 i 处局部法向（前后点估切线再转 90 度）。"""
    n = len(c)
    prev = c[(i - 1) % n]
    nxt = c[(i + 1) % n]
    tx, ty = nxt.x - prev.x, nxt.y - prev.y
    L = math.hypot(tx, ty)
    if L < 1e-9:
        return (1.0, 0.0)
    return (-ty / L, tx / L)


def thickness_at(contours, ci, i, edges=None, max_ray=500.0):
    """第 ci 轮廓第 i 点沿法向（两方向取最近）命中的厚度。"""
    if edges is None:
        edges = all_edges(contours)
    c = contours[ci]
    p = c[i]
    nx, ny = local_normal(c, i)
    best = None
    for sign in (1.0, -1.0):
        d = (nx * sign, ny * sign)
        for (a, b, oi) in edges:
            if oi == ci:
                continue  # 同轮廓跳过，避免自命中
            t = _seg_intersect((p.x, p.y), d, a, b)
            if t is not None and t < max_ray:
                if best is None or t < best:
                    best = t
    return best


def measure_all(contours, step=2):
    """返回 {contour_index: [thickness 或 None]}。"""
    edges = all_edges(contours)
    out = {}
    for ci, c in enumerate(contours):
        vals = []
        for i in range(len(c)):
            vals.append(None if i % step else thickness_at(contours, ci, i, edges))
        out[ci] = vals
    return out


def stroke_width_estimate(contours):
    """字体级笔画宽度：所有法向厚度的中位数。"""
    vals = []
    for _, row in measure_all(contours).items():
        for v in row:
            if v is not None and 5 < v < 250:
                vals.append(v)
    if not vals:
        return 50.0
    vals.sort()
    return vals[len(vals) // 2]
