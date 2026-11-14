# -*- coding: utf-8 -*-
"""把 transforms.py 的形态算子接入主构建管线（P94）。

## 背景

调查发现当前母版由 p1_edge.py 产出，它**只调用 thin_edges**：
  done, skip = T.thin_edges(f, D_H, D_V)
全文没有第二处形态操作。

而用户指出的五个问题，恰好对应五个从未被调用的算子：
  笔末凹进  terminal_fix
  喇叭口    flatten_flare
  去出脚    feet_removal
  钩张力    hook_tension
  点柔化    dot_normalize
这些算子在 tools/transforms.py 里**都已实现**，但只在 make_new.py /
p0_pipeline.py（单字试验）中用过，从未进入生产管线。

## 桥接方案

thinning.py  操作 glyf 原始点（coordinates + endPtsOfContours）
transforms.py 操作 RecordingPen.value  ((op, args) 列表)

两者都保证「只移动节点、不增删」，所以可以互相转换：
  glyf -> RecordingPen.value  (quadratic TrueType: qCurveTo)
  RecordingPen.value -> glyf  (按 on/off 还原)

注意：TrueType 是二次曲线，点序为 [on, off, off, ...]，
与 cubic 的 curveTo 不同。转换必须保留 off 点数量。
"""
from __future__ import annotations
import math
import sys


def glyf_to_value(glyph):
    """glyf Glyph -> RecordingPen.value（qCurveTo 形式，保留全部点）。"""
    if glyph.numberOfContours <= 0:
        return None
    coords = list(glyph.coordinates)
    ends = list(glyph.endPtsOfContours)
    flags = list(glyph.flags)
    if hasattr(flags[0], "__len__"):
        # flags 可能是 Flag 对象列表
        flags = [int(f) for f in flags]

    value = []
    start = 0
    for e in ends:
        pts = [(float(coords[i][0]), float(coords[i][1]), bool(flags[i] & 1))
               for i in range(start, e + 1)]
        start = e + 1
        if not pts:
            continue
        # 找第一个 on 点作为起点（若全 off，取首点）
        k = next((i for i, p in enumerate(pts) if p[2]), None)
        if k is None:
            value.append(("moveTo", ((pts[0][0], pts[0][1]),)))
            value.append(("qCurveTo", tuple((p[0], p[1]) for p in pts[1:])))
            value.append(("closePath", ()))
            continue
        value.append(("moveTo", ((pts[k][0], pts[k][1]),)))
        # 从 k+1 绕一圈回到 k
        seq = [pts[(k + i) % len(pts)] for i in range(1, len(pts) + 1)]
        # 末尾的 k 本身是「回到起点」，不进 qCurveTo
        body = seq[:-1]
        if body:
            value.append(("qCurveTo", tuple((p[0], p[1]) for p in body)))
        value.append(("closePath", ()))
    return value


def value_to_glyf(value, glyph):
    """RecordingPen.value -> 写回 glyf Glyph（点数必须一致）。"""
    pts = []
    for op, args in value:
        if op == "moveTo":
            x, y = args[0]
            pts.append((x, y, True))
        elif op == "lineTo":
            x, y = args[0]
            pts.append((x, y, True))
        elif op in ("qCurveTo", "curveTo"):
            for p in args:
                if p is None:
                    continue
                pts.append((p[0], p[1], op == "lineTo"))
        elif op in ("closePath", "endPath"):
            continue
    # qCurveTo 的最后一个点是 on（TrueType 规范）
    return pts


def apply_to_glyph(glyph, params, transforms_mod):
    """对单个 glyf 字形应用 transforms 算子链，原位写回。

    返回 (成功?, 原始点数, 新点数)。点数不一致则拒绝写回。
    """
    val = glyf_to_value(glyph)
    if val is None:
        return False, 0, 0
    n_before = sum(len(a) for op, a in val if op in ("moveTo", "lineTo", "qCurveTo"))

    try:
        out = transforms_mod.apply_all(val, params)
    except Exception as e:
        return False, n_before, n_before

    pts = value_to_glyf(out, glyph)
    if len(pts) != n_before:
        return False, n_before, len(pts)

    from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates
    gc = GlyphCoordinates([(int(round(x)), int(round(y))) for x, y, on in pts])
    gc.toInt()
    newflags = bytearray(len(pts))
    for i, (x, y, on) in enumerate(pts):
        newflags[i] = 1 if on else 0
    glyph.coordinates = gc
    glyph.flags = newflags
    for a in ("xMin", "yMin", "xMax", "yMax"):
        if hasattr(glyph, a):
            delattr(glyph, a)
    return True, n_before, len(pts)