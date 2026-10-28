#!/usr/bin/env python3
"""验证 CV 修复：用 SHS 原始轮廓跑 GlyphModel，再 restore，比较 on/off 结构。"""
import sys

sys.path.insert(0, '/opt/wdsans/vendor/glow-src/src/cv')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from glyph_model import GlyphModel

FONT = '/opt/wdsans/ref/shs/shs-400.otf'
CP = 0x5C81  # 岁

t = TTFont(FONT, lazy=True)
gs = t.getGlyphSet()
cm = t.getBestCmap()
pen = RecordingPen()
gs[cm[CP]].draw(pen)

contours = []
for op, args in pen.value:
    if op == 'moveTo':
        contours.append([{'x': args[0][0], 'y': args[0][1], 'on': True}])
    elif op == 'lineTo':
        contours[-1].append({'x': args[0][0], 'y': args[0][1], 'on': True})
    elif op == 'curveTo':
        for a in args[:2]:
            contours[-1].append({'x': a[0], 'y': a[1], 'on': False})
        contours[-1].append({'x': args[2][0], 'y': args[2][1], 'on': True})

print('原始:', ''.join('O' if p['on'] else '.' for p in contours[0][:20]),
      f"| 点 {len(contours[0])}")

m = GlyphModel(contours)
out = m.restore()
print('重建:', ''.join('O' if p['on'] else '.' for p in out[0][:20]),
      f"| 点 {len(out[0])}")

from collections import Counter
c = Counter(m.off_on_indices)
print('每个 on 挂的 off 数:', dict(Counter(c.values())))

# 逐点比对
maxd = 0
n = 0
for ca, cb in zip(contours, out):
    if len(ca) != len(cb):
        print('轮廓长不同', len(ca), len(cb))
        break
    for pa, pb in zip(ca, cb):
        maxd = max(maxd, abs(pa['x'] - pb['x']), abs(pa['y'] - pb['y']))
        n += 1
print(f'逐点 {n} 最大差 {maxd:.1f}')
