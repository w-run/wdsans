"""几何算子：改写 glyf base 轮廓（改变默认实例）。

五条实测结论（每条都来自看图 + 测量，不是推断）：
  1. instancer 重设轴后 glyf base = wght=400 实际轮廓；
     gvar delta 只是相对 400 的偏移，只影响 400 以外的字重。
  2. 等比缩放**不改变墨密度**（面积与 bbox 同比缩放）。
  3. Noto 的轮廓绕向**不统一**（口两轮廓都是负面积，国却不一致），
     所以「按绕向定法向」和「按嵌套定洞」都会误判。
  4. 正确做法：**逐轮廓自校准** —— 试 ±d，取让净墨面积变小的那个。
  5. 质心收缩会把含隐含中点的轮廓角点拉歪，不要用。
"""
from __future__ import annotations
import math

from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

CX, CY = 500.0, 500.0


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


def _offset(seg, d):
    """沿法向偏移 d（正负由调用方定）。"""
    n = len(seg)
    out = []
    for i in range(n):
        px, py = seg[i]
        ax, ay = seg[(i - 1) % n]
        bx, by = seg[(i + 1) % n]
        tx, ty = bx - ax, by - ay
        L = math.hypot(tx, ty)
        if L < 1e-9:
            out.append((px, py))
            continue
        nx, ny = -ty / L, tx / L
        out.append((px + nx * d, py + ny * d))
    return out


def _commit(g, pts):
    gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y in pts])
    gc.toInt()
    g.coordinates = gc
    for attr in ("xMin", "yMin", "xMax", "yMax"):
        if hasattr(g, attr):
            delattr(g, attr)


def thin_glyph_segments(segs, d):
    """逐轮廓自校准减细：每个轮廓单独试 ±d，取净墨面积更小者。"""
    out = []
    for seg in segs:
        if len(seg) < 3:
            out.append(seg)
            continue
        a0 = abs(_area(seg))
        cand = []
        for sgn in (d, -d):
            s2 = _offset(seg, sgn)
            cand.append((abs(_area(s2)), s2))
        cand.sort(key=lambda x: x[0])
        # 只有确实变小才采纳，否则保持原样（避免把退化轮廓弄得更糟）
        out.append(cand[0][1] if cand[0][0] < a0 else seg)
    return out


def thin_strokes_base(font, d):
    """全部简单字形减细 d 单位。点数/顺序/on-off 不变。"""
    glyf = font["glyf"]
    done = skipped = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            skipped += 1
            continue
        coords = list(g.coordinates)
        ends = list(g.endPtsOfContours) + [len(coords)]
        segs = []
        start = 0
        for e in ends:
            segs.append(coords[start:e])
            start = e
        new = [p for s in thin_glyph_segments(segs, d) for p in s]
        assert len(new) == len(coords), f"{name}: 点数变了"
        _commit(g, new)
        done += 1
    return done, skipped


def face_scale_base(font, sx, sy=None, cx=CX, cy=CY):
    if sy is None:
        sy = sx
    glyf = font["glyf"]
    n = 0
    for name in font.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours <= 0:
            continue
        out = [((x - cx) * sx + cx, (y - cy) * sy + cy) for (x, y) in g.coordinates]
        _commit(g, out)
        n += 1
    return n


def assert_unchanged_topology(glyf_a, glyf_b, names):
    for name in names:
        a, b = glyf_a[name], glyf_b[name]
        if a.numberOfContours != b.numberOfContours:
            raise AssertionError(f"{name}: 轮廓数变了")
        if a.numberOfContours > 0:
            if len(a.coordinates) != len(b.coordinates):
                raise AssertionError(f"{name}: 点数变了")
            if list(a.flags) != list(b.flags):
                raise AssertionError(f"{name}: on/off 变了")
    return True
