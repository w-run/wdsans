#!/usr/bin/env python3
"""audit_latin - 逐字对比 我们 vs Mona，确认 1.082 的来源"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
MONA = '/workspace/wdsans/ref/mona/MonaSansVF.ttf'


def info(path, ch, wght=None):
    f = TTFont(path, lazy=True)
    if wght is not None and "fvar" in f:
        from fontTools.varLib.instancer import instantiateVariableFont
        f = instantiateVariableFont(f, {"wght": wght}, inplace=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    bp = BoundsPen(gs)
    gs[cm[ord(ch)]].draw(bp)
    adv = f["hmtx"][cm[ord(ch)]][0]
    f.close()
    if not bp.bounds:
        return None
    b = bp.bounds
    return b[2]-b[0], adv, b[0], b[2]


print('%-4s %-22s %-22s %-8s' % ('字', '我们 (墨宽/adv)', 'Mona@400 (墨宽/adv)', '比'))
rows = []
for ch in 'HAMBURGEhamn0eo':
    a = info(VF, ch)
    b = info(MONA, ch, 400)
    if not a or not b:
        continue
    r = a[0] / b[0]
    rows.append(r)
    print('%-4s %-22s %-22s %-8.3f' % (ch, '%4.0f / %4.0f' % (a[0], a[1]), '%4.0f / %4.0f' % (b[0], b[1]), r))

import numpy as np
if rows:
    print()
    print('墨宽比 中位 %.3f 均值 %.3f' % (np.median(rows), np.mean(rows)))
    print('adv 比对照:')
for ch in 'HAMW':
    a = info(VF, ch); b = info(MONA, ch, 400)
    if a and b:
        print('  %s adv 我们=%d Mona=%d 比%.3f' % (ch, a[1], b[1], a[1]/b[1]))