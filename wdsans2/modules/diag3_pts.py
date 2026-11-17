#!/usr/bin/env python3
"""diag3_pts - 打印 到/出/永 关键轮廓的精确点坐标"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'


def pts_of(path, ch, ci):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    parts = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: parts.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: parts.append((start, segs))
            start = None; segs = None
    if start is not None: parts.append((start, segs))
    st, sg = parts[ci]
    out = [("start", st)]
    for op, args in sg:
        for p in args:
            out.append((op, p))
    return out


print('=== 到 c3 (顶部横笔, LLL) ===')
for lbl, path in [('我们', VF), ('SHS', SHS)]:
    if lbl == '我们':
        for tag, p in pts_of(path, '到', 3):
            print('  %-6s %-7s (%.1f, %.1f)' % (lbl, tag, p[0], p[1]))
    else:
        print('  %s c3 是合并轮廓，跳过' % lbl)

print()
print('=== 出 c1/c3 (右下脚) ===')
for ci in (1, 3):
    print('  c%d:' % ci)
    for tag, p in pts_of(VF, '出', ci):
        print('     %-7s (%.1f, %.1f)' % (tag, p[0], p[1]))

print()
print('=== 永 c4 (竖弯钩, LLLCCCCC) ===')
for tag, p in pts_of(VF, '永', 4):
    print('  %-7s (%.1f, %.1f)' % (tag, p[0], p[1]))