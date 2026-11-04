"""笔画角色识别。

取代 glow-sans 的固定阈值判据（detect-feet.js 用 7 点窗口 + 2° 直角容差，
字重一变就失效 —— 见 docs/UPSTREAM-DEFECTS.md A1）。

这里改用**几何不变量**判据，且结果落盘为 JSON，可人工覆盖：
  build/roles/<glyph>.json
"""
from __future__ import annotations
import json
import math
import os

ROLE_END = "end"      # 笔画端面
ROLE_FOOT = "foot"    # 出脚（竖画顶端小方突）
ROLE_CORNER = "corner"  # 折角
ROLE_HOOK = "hook"    # 钩


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def _angle(ax, ay, bx, by, cx, cy):
    """B 处的夹角（度），A-B-C。"""
    v1 = (ax - bx, ay - by)
    v2 = (cx - bx, cy - by)
    n1 = math.hypot(*v1)
    n2 = math.hypot(*v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cosv = max(-1.0, min(1.0, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2)))
    return math.degrees(math.acos(cosv))


def detect_ends(contour, stroke_w: float, angle_tol: float = 25.0):
    """笔画端面：连续 on,off,off,on 结构，两端距离 ≈ 笔画宽度。

    对应 glow 的 detect-ends.js，但容差放宽且以**笔画宽度实测值**为准，
    而不是写死的 maxStroke。
    """
    n = len(contour)
    hits = []
    for i in range(n):
        p1 = contour[i]
        p2 = contour[(i + 1) % n]
        p3 = contour[(i + 2) % n]
        p4 = contour[(i + 3) % n]
        p5 = contour[(i + 4) % n]
        p6 = contour[(i + 5) % n]
        if p1.on or not p2.on or p3.on or p4.on or not p5.on or p6.on:
            continue
        width = _dist(p2, p5)
        if width > stroke_w * 1.6:
            continue
        a1 = _angle(p5.x, p5.y, p2.x, p2.y, p1.x, p1.y)
        a2 = _angle(p6.x, p6.y, p5.x, p5.y, p2.x, p2.y)
        if abs((a1 + a2) - 160.0) > angle_tol:
            continue
        hits.append((i + 1) % n)
    return hits


def detect_corners(contour, min_turn: float = 70.0):
    """折角：相邻两个 on 点之间的转向角 ≥ min_turn。"""
    hits = []
    on_idx = [i for i, p in enumerate(contour) if p.on]
    if len(on_idx) < 3:
        return hits
    for k in range(len(on_idx)):
        i0 = on_idx[k - 1]
        i1 = on_idx[k]
        i2 = on_idx[(k + 1) % len(on_idx)]
        a = _angle(contour[i0].x, contour[i0].y,
                   contour[i1].x, contour[i1].y,
                   contour[i2].x, contour[i2].y)
        turn = abs(180.0 - a)
        if turn >= min_turn:
            hits.append(i1)
    return hits


def measure_stroke_width(contours) -> float:
    """粗估笔画宽度：所有轮廓 bbox 的短边中位数 × 0.5。

    只用于给识别器一个尺度量级，不作为最终判据。
    """
    boxes = []
    for c in contours:
        xs = [p.x for p in c]
        ys = [p.y for p in c]
        if not xs:
            continue
        boxes.append((max(xs) - min(xs), max(ys) - min(ys)))
    if not boxes:
        return 50.0
    short = sorted(min(b) for b in boxes)
    mid = short[len(short) // 2]
    return max(10.0, mid * 0.5)


def roles_for_glyph(contours, stroke_w=None):
    if stroke_w is None:
        stroke_w = measure_stroke_width(contours)
    out = {"stroke_width": round(stroke_w, 2), "contours": []}
    for ci, c in enumerate(contours):
        out["contours"].append({
            "index": ci,
            "ends": detect_ends(c, stroke_w),
            "corners": detect_corners(c),
            "n_points": len(c),
        })
    return out
