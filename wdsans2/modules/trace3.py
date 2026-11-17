#!/usr/bin/env python3
"""trace3 - 逐阶段溯源 到/出/永 三处缺陷的引入点"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

BASE = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',  BASE + 'masters_T6/master-Regular-400.otf'),
  ('MOD', BASE + 'masters_MOD/master-Regular-400.otf'),
  ('R1',  BASE + 'masters_R1/master-Regular-400.otf'),
  ('R4',  BASE + 'masters_R4/master-Regular-400.otf'),
  ('R10', BASE + 'masters_R10/master-Regular-400.otf'),
  ('R15', BASE + 'masters_R15/master-Regular-400.otf'),
  ('R16', BASE + 'masters_R16/master-Regular-400.otf'),
  ('R25b',BASE + 'masters_R25b/master-Regular-400.otf'),
  ('VF',  '/workspace/static/wdsans/WDesignSans-VF.otf'),
]


def parts(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen()
    try:
        gs[cm[ord(ch)]].draw(rp)
    except Exception:
        f.close(); return None
    f.close()
    out = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: out.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: out.append((start, segs))
            start = None; segs = None
    if start is not None: out.append((start, segs))
    return out


def row_scan(path, ch, y, tol=1.5):
    """返回 y 处的墨段 x 区间列表（用轮廓求交）"""
    ps = parts(path, ch)
    if not ps:
        return []
    segs = []
    for st, sg in ps:
        prev = np.array(st, float)
        for op, args in sg:
            if op == "lineTo":
                p = np.array(args[0], float)
                segs.append((prev, p)); prev = p
            elif op in ("curveTo","qCurveTo"):
                a = args
                ctrl = [np.array(x, float) for x in a]
                # 用折线近似
                pts = [prev] + ctrl
                for k in range(len(pts)-1):
                    segs.append((pts[k], pts[k+1]))
                prev = ctrl[-1]
    xs = []
    for p0, p1 in segs:
        if abs(p0[1] - p1[1]) < 1e-9:
            if abs(y - p0[1]) < tol:
                xs.extend([p0[0], p1[0]])
            continue
        if min(p0[1], p1[1]) - tol <= y <= max(p0[1], p1[1]) + tol:
            t = (y - p0[1]) / (p1[1] - p0[1])
            if -0.05 <= t <= 1.05:
                xs.append(p0[0] + t * (p1[0] - p0[0]))
    xs = sorted(xs)
    if not xs:
        return []
    runs = [[xs[0], xs[0]]]
    for x in xs[1:]:
        if x - runs[-1][1] <= 3:
            runs[-1][1] = x
        else:
            runs.append([x, x])
    return [(round(a), round(b)) for a, b in runs if b - a > 1]


print('=' * 62)
print('【到】顶部横笔右端逐阶段 (y=740)')
print('=' * 62)
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    r = row_scan(p, '到', 740)
    print('  %-5s %s' % (lbl, r))

print()
print('=' * 62)
print('【出】右下脚逐阶段 (y=-50)')
print('=' * 62)
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    r = row_scan(p, '出', -50)
    print('  %-5s %s' % (lbl, r))

print()
print('=' * 62)
print('【永】竖弯钩底部逐阶段 (y=-30)')
print('=' * 62)
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    r = row_scan(p, '永', -30)
    print('  %-5s %s' % (lbl, r))