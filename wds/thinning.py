"""按笔画方向减细（边级判据 + 斜接，修正轮廓切分）。

本轮定位到的关键 bug（都来自实测，不是推断）：
  1. endPtsOfContours 是**结束索引**，不是点数。
     「一」的 endPts=[3] 表示「1 个轮廓、4 个点」。
     旧代码写 ends = endPts + [len(coords)]，导致多切出一个空段，
     真实轮廓被拆成 [3点, 1点] → 边判据全部错位 → 横厚改不动。
  2. 点级法向在角点处由对角线决定，判据混乱。
  3. 角点必须取相邻两边位移的**矢量和**（斜接），不能取平均。
"""
from __future__ import annotations
import math

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates


def split_contours(g):
    """正确切分 glyf 轮廓：endPtsOfContours 是结束索引（含）。"""
    coords = list(g.coordinates)
    segs = []
    start = 0
    for end in g.endPtsOfContours:
        segs.append(coords[start:end + 1])
        start = end + 1
    return segs


def _area(seg):
    n = len(seg)
    if n < 3:
        return 0.0
    a = 0.0
    for i in range(n):
        x1, y1 = seg[i]
        x2, y2 = seg[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def _offset_miter(seg, d_h, d_v, sign):
    """每条边按自身法向平移，角点取相邻两条偏移线的交点（精确斜接）。

    P93：原实现用法向矢量和，仅在 90 度角正确；钝角处会超出 1.7 倍，
    导致斜边反而被拉长。改为求交点，对任意角度精确。
    """
    n = len(seg)
    if n < 3:
        return seg

    def offset_line(i, j):
        """返回边(i->j)的偏移直线：(点, 方向)。"""
        x1, y1 = seg[i]
        x2, y2 = seg[j]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-9:
            return None
        nx, ny = -dy / L, dx / L
        # 水平边（法向竖直）用 d_h，竖直边（法向水平）用 d_v
        d = d_h if abs(ny) >= abs(nx) else d_v
        return ((x1 + nx * d * sign, y1 + ny * d * sign), (dx, dy))

    lines = [offset_line(k, (k + 1) % n) for k in range(n)]

    def intersect(l1, l2):
        """两直线交点；平行时返回 None。"""
        if l1 is None or l2 is None:
            return None
        (p1, d1), (p2, d2) = l1, l2
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            return None
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        return (p1[0] + d1[0] * t, p1[1] + d1[1] * t)

    out = []
    for k in range(n):
        prev = (k - 1) % n
        pt = intersect(lines[prev], lines[k])
        if pt is None:
            # 平行退化：退回单边法向平移
            l = lines[k] if lines[k] else lines[prev]
            if l is None:
                out.append(seg[k])
            else:
                (px, py), (dx, dy) = l
                L = math.hypot(dx, dy)
                nx, ny = -dy / L, dx / L
                d = d_h if abs(ny) >= abs(nx) else d_v
                out.append((seg[k][0] + nx * d * sign, seg[k][1] + ny * d * sign))
            continue
        # 抑制极端斜接（锐角处交点会飞很远）
        mx = (seg[k][0] + pt[0]) / 2
        my = (seg[k][1] + pt[1]) / 2
        maxmove = 3.0 * max(d_h, d_v)
        if math.hypot(pt[0] - seg[k][0], pt[1] - seg[k][1]) > maxmove:
            out.append((mx, my))
        else:
            out.append(pt)
    return out


def _commit(g, pts):
    gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in pts])
    gc.toInt()
    g.coordinates = gc
    for a in ("xMin", "yMin", "xMax", "yMax"):
        if hasattr(g, a):
            delattr(g, a)


def thin_edges(font, d_h, d_v):
    """边级方向减细。横边减 2*d_h，竖边减 2*d_v。逐轮廓自校准。"""
    glyf = font["glyf"]
    done = skipped = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            skipped += 1
            continue
        segs = split_contours(g)
        n_before = sum(len(s) for s in segs)
        out = []
        for seg in segs:
            if len(seg) < 3:
                out.extend(seg)
                continue
            a0 = abs(_area(seg))
            best = None
            for sign in (1.0, -1.0):
                s2 = _offset_miter(seg, d_h, d_v, sign)
                a2 = abs(_area(s2))
                if best is None or a2 < best[0]:
                    best = (a2, s2)
            out.extend(best[1] if best[0] < a0 else seg)
        assert len(out) == n_before, f"{name}: 点数变了 {n_before}->{len(out)}"
        _commit(g, out)
        done += 1
    return done, skipped
