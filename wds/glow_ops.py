# -*- coding: utf-8 -*-
"""glow-sans 几何算子的 Python 复刻（P92）。

## 来源

直接移植自 vendor/glow-src/src/glyph-manipulate/ 下的：
  detect-ends.js     笔末检测（6 点模式）
  detect-feet.js     出脚检测（7 点模式）
  PostFilters.js     strokeEndsFlatten / hookTension / softenDots

## 为什么移植

用户指出当前字体：笔末凹进未做、喇叭口未做、曲线变形、去脚致畸、笔画不均。
glow-sans 对这五个问题**都有已实现的算子**，只是它跑在栅格化路线上。
我们把它搬到节点位移路线上，先追赶、后超越。

## 与原文的差异

原文用 {x,y,on} 对象；我们用 fontTools 的 (x, y, on) 元组，结构等价。
所有算子输入输出都是 「轮廓列表 = [[(x,y,on), ...], ...]」。
"""
from __future__ import annotations
import math


def _tuple(p):
    return (p[0], p[1])


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle(a, b, c):
    """b 为顶点，返回角 abc（度）。"""
    v1 = (a[0] - b[0], a[1] - b[1])
    v2 = (c[0] - b[0], c[1] - b[1])
    d = math.hypot(*v1) * math.hypot(*v2)
    if d == 0:
        return 0.0
    cos = max(-1.0, min(1.0, (v1[0]*v2[0] + v1[1]*v2[1]) / d))
    return math.degrees(math.acos(cos))


def _projection(p, a, b):
    """点 p 到直线 ab 上的投影。"""
    abx, aby = b[0] - a[0], b[1] - a[1]
    L2 = abx*abx + aby*aby
    if L2 == 0:
        return p
    t = ((p[0]-a[0])*abx + (p[1]-a[1])*aby) / L2
    return (a[0] + t*abx, a[1] + t*aby)


# ---------------- detect-ends.js ----------------

def is_end(c, i, max_stroke=10, angle_tol=20):
    """6 点模式：off,on,off,off,on,off 且两段夹角和≈160°。"""
    n = len(c)
    p1 = c[i % n]; p2 = c[(i+1) % n]; p3 = c[(i+2) % n]
    p4 = c[(i+3) % n]; p5 = c[(i+4) % n]; p6 = c[(i+5) % n]
    # on/off 模式：p1 off, p2 on, p3 off, p4 off, p5 on, p6 off
    if p1[2] or not p2[2] or p3[2] or p4[2] or not p5[2] or p6[2]:
        return False
    if _dist(_tuple(p2), _tuple(p5)) > max_stroke * 1.4:
        return False
    a1 = _angle(_tuple(p5), _tuple(p2), _tuple(p1))
    a2 = _angle(_tuple(p6), _tuple(p5), _tuple(p2))
    if abs(a1 + a2 - 160) >= angle_tol:
        return False
    return True


def detect_ends(contour, max_stroke=10, angle_tol=20):
    n = len(contour)
    return [(i+1) % n for i in range(n)
            if is_end(contour, i, max_stroke, angle_tol)]


# ---------------- PostFilters: strokeEndsFlatten ----------------

def _target_points(c, end_index):
    """返回笔末 4 个目标点 tp2/tp3/tp4/tp5。"""
    n = len(c)
    p1 = _tuple(c[(end_index-1) % n])
    p2 = _tuple(c[end_index])
    p5 = _tuple(c[(end_index+3) % n])
    p6 = _tuple(c[(end_index+4) % n])
    p2p = _projection(p2, p5, p6)
    p5p = _projection(p5, p2, p1)
    tp20 = ((p5p[0]+p2[0])*0.5, (p5p[1]+p2[1])*0.5)
    tp50 = ((p2p[0]+p5[0])*0.5, (p2p[1]+p5[1])*0.5)
    r = 0
    tp2 = (tp20[0]*(1-r) + tp50[0]*r, tp20[1]*(1-r) + tp50[1]*r)
    tp5 = (tp50[0]*(1-r) + tp20[0]*r, tp50[1]*(1-r) + tp20[1]*r)
    tp3 = (tp2[0]*0.3 + tp5[0]*0.7, tp2[1]*0.3 + tp5[1]*0.7)
    tp4 = (tp2[0]*0.7 + tp5[0]*0.3, tp2[1]*0.7 + tp5[1]*0.3)
    return tp2, tp3, tp4, tp5


def stroke_ends_flatten(contour, ratio=0.7, max_stroke=10, angle_tol=20):
    """笔末凹进/压平：把钩、撇捺的末端收成斜面。"""
    n = len(contour)
    ends = detect_ends(contour, max_stroke, angle_tol)
    if not ends:
        return contour
    targets = {}
    for e in ends:
        tp2, tp3, tp4, tp5 = _target_points(contour, e)
        targets[e] = tp2
        targets[(e+1) % n] = tp3
        targets[(e+2) % n] = tp4
        targets[(e+3) % n] = tp5
    out = []
    for i, pt in enumerate(contour):
        if i not in targets:
            out.append(pt); continue
        t = targets[i]
        x = pt[0]*(1-ratio) + t[0]*ratio
        y = pt[1]*(1-ratio) + t[1]*ratio
        out.append((x, y, pt[2]))
    return out


# ---------------- PostFilters: hookTension ----------------

def _is_hook(c, i):
    n = len(c)
    p1 = c[i % n]; p2 = c[(i+1) % n]; p3 = c[(i+2) % n]
    p4 = c[(i+3) % n]; p5 = c[(i+4) % n]; p6 = c[(i+5) % n]
    # off off on on off off
    if p1[2] or p2[2] or not p3[2] or not p4[2] or p5[2] or p6[2]:
        return False
    if abs(p3[1]-p2[1]) > 1 or abs(p4[1]-p3[1]) > 1 or abs(p5[1]-p4[1]) > 1:
        return False
    return (p1[1] > p2[1]) and (p6[1] > p5[1])


def hook_tension(contour, ratio=0.35):
    """水平钩的张力：把钩中间两点向中心收，形成喇叭口收束。"""
    n = len(contour)
    out = list(contour)
    for i in range(n):
        if not _is_hook(out, i):
            continue
        i3 = (i+2) % n; i4 = (i+3) % n
        p3 = out[i3]; p4 = out[i4]
        cx = (p3[0] + p4[0]) / 2
        out[i3] = (p3[0]*(1-ratio) + cx*ratio, p3[1], p3[2])
        out[i4] = (p4[0]*(1-ratio) + cx*ratio, p4[1], p4[2])
    return out


# ---------------- PostFilters: softenDots ----------------

def _is_dot(contour, max_stroke=10):
    if len(contour) != 8:
        return False
    c = contour
    nearest = None
    if c[1][2]:
        ok = (not c[2][2]) and (not c[3][2]) and c[4][2] and c[5][2] \
             and (not c[6][2]) and (not c[7][2])
        if not ok: return False
        nearest = c[1]
    elif c[7][2]:
        ok = (not c[1][2]) and (not c[2][2]) and c[3][2] and c[4][2] \
             and (not c[5][2]) and (not c[6][2])
        if not ok: return False
        nearest = c[7]
    else:
        return False
    if _dist(_tuple(c[0]), _tuple(nearest)) >= max_stroke:
        return False
    return _angle(_tuple(c[2]), _tuple(c[1]), _tuple(c[0])) < 180


def soften_dots(contour, value=0.5, max_stroke=10):
    """点柔化：把圆点的 off 点向对边投影靠拢，避免尖锐。"""
    if not _is_dot(contour, max_stroke):
        return contour
    n = len(contour)
    out = []
    for i, pt in enumerate(contour):
        if pt[2]:
            out.append(pt); continue
        prev = contour[(i-1) % n]
        prev_on = prev if prev[2] else contour[(i-2) % n]
        nxt = contour[(i+1) % n]
        nxt_on = nxt if nxt[2] else contour[(i+2) % n]
        t = _projection(_tuple(pt), _tuple(prev_on), _tuple(nxt_on))
        x = value*pt[0] + (1-value)*t[0]
        y = value*pt[1] + (1-value)*t[1]
        out.append((x, y, False))
    return out


def apply_all(contours, cfg):
    """按 glow-sans 顺序应用全部算子。"""
    ms = cfg.get("max_stroke", 10)
    out = []
    for c in contours:
        if cfg.get("soften_dots"):
            c = soften_dots(c, cfg.get("dot_value", 0.5), ms)
        if cfg.get("hook_tension"):
            c = hook_tension(c, cfg.get("hook_ratio", 0.35))
        if cfg.get("flatten_ends"):
            c = stroke_ends_flatten(c, cfg.get("end_ratio", 0.7), ms,
                                    cfg.get("angle_tol", 20))
        out.append(c)
    return out