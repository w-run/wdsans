#!/usr/bin/env python3
"""渲染级字形对比：把两个字体的同码位字形光栅化后算像素差异。

为什么不用曲线数比对：
  - CFF(三次) 与 TTF(二次) 的曲线数天然不可比
  - 端点处理/去脚本来就会改变曲线数量
  → 曲线数只能当"变化提示"，不能当"质量判据"

像素 diff 才是"看上去对不对"的可靠代理。

用法:
    python3 qa/render_diff.py --ref A.otf --cur B.otf [--size 64] [--limit 500]
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont


class PolyPen(BasePen):
    """把轮廓收集成多边形（由 FlattenPen 驱动，曲线已被切分）。"""

    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.polys = []
        self.cur = []

    def _moveTo(self, pt):
        if len(self.cur) >= 3:
            self.polys.append(self.cur)
        self.cur = [pt]

    def _lineTo(self, pt):
        self.cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8.0
            mt = 1 - t
            self.cur.append((
                mt**3 * p0[0] + 3 * mt * mt * t * p1[0]
                + 3 * mt * t * t * p2[0] + t**3 * p3[0],
                mt**3 * p0[1] + 3 * mt * mt * t * p1[1]
                + 3 * mt * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self.cur[-1]
        for i in range(1, 9):
            t = i / 8.0
            mt = 1 - t
            self.cur.append((
                mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self.cur) >= 3:
            self.polys.append(self.cur)
        self.cur = []

    def _endPath(self):
        self._closePath()


def rasterize(glyph_set, gname, size=64, upm=1000):
    """even-odd 射线法光栅化，返回 bool 位图（True=墨迹）。"""
    pen = PolyPen(glyph_set)
    try:
        glyph_set[gname].draw(pen)
    except Exception:
        return None
    polys = pen.polys + ([pen.cur] if len(pen.cur) >= 3 else [])
    if not polys:
        return np.zeros((size, size), dtype=bool)

    scale = size / upm
    yy, xx = np.mgrid[0:size, 0:size]
    px = (xx + 0.5) / scale
    py = (size - yy - 0.5) / scale

    inside = np.zeros((size, size), dtype=bool)
    for poly in polys:
        n = len(poly)
        if n < 3:
            continue
        pts = np.array(poly, dtype=np.float64)
        x1, y1 = pts[:, 0], pts[:, 1]
        x2, y2 = np.roll(x1, -1), np.roll(y1, -1)
        for i in range(n):
            cond = (y1[i] > py) != (y2[i] > py)
            if not cond.any():
                continue
            with np.errstate(divide='ignore', invalid='ignore'):
                xint = x1[i] + (py - y1[i]) * (x2[i] - x1[i]) / (y2[i] - y1[i])
            inside ^= cond & (px < xint)
    return inside


def diff_score(a, b):
    """返回 0..1，0 表示完全一致。用墨迹并集归一化，避免小字失真。"""
    if a is None or b is None:
        return None
    union = (a | b).sum()
    if union == 0:
        return 0.0
    return float((a ^ b).sum()) / float(union)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True)
    ap.add_argument('--cur', required=True)
    ap.add_argument('--size', type=int, default=64)
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--report', default='')
    ap.add_argument('--top', type=int, default=20)
    a = ap.parse_args()

    t1 = TTFont(a.ref, lazy=True)
    t2 = TTFont(a.cur, lazy=True)
    gs1, gs2 = t1.getGlyphSet(), t2.getGlyphSet()
    cm1, cm2 = t1.getBestCmap(), t2.getBestCmap()
    cps = sorted(set(cm1) & set(cm2))
    # 只比 CJK 与常用符号
    cps = [c for c in cps if 0x20 <= c <= 0xFFFF]
    if a.limit:
        cps = cps[:a.limit]

    scores = []
    for cp in cps:
        d = diff_score(rasterize(gs1, cm1[cp], a.size),
                       rasterize(gs2, cm2[cp], a.size))
        if d is not None:
            scores.append((d, cp))

    if not scores:
        print('无可比字形')
        return
    vals = np.array([s for s, _ in scores])
    print(json.dumps({
        'compared': len(scores),
        'mean': round(float(vals.mean()), 4),
        'median': round(float(np.median(vals)), 4),
        'p95': round(float(np.percentile(vals, 95)), 4),
        'p99': round(float(np.percentile(vals, 99)), 4),
        'max': round(float(vals.max()), 4),
        'over_10pct': int((vals > 0.10).sum()),
        'over_25pct': int((vals > 0.25).sum()),
    }, ensure_ascii=False, indent=1))

    scores.sort(reverse=True)
    print(f'\n差异最大的 {a.top} 个：')
    for d, cp in scores[:a.top]:
        print(f'  U+{cp:04X} {chr(cp)}  {d*100:.1f}%')

    if a.report:
        os.makedirs(os.path.dirname(a.report) or '.', exist_ok=True)
        with open(a.report, 'w') as f:
            json.dump({'ref': a.ref, 'cur': a.cur, 'size': a.size,
                       'scores': [{'cp': f'U+{cp:04X}', 'char': chr(cp),
                                   'diff': round(d, 4)} for d, cp in scores]},
                      f, ensure_ascii=False, indent=1)
        print(f'\n报告 -> {a.report}')


if __name__ == '__main__':
    main()
