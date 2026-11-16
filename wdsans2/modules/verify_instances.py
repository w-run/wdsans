#!/usr/bin/env python3
"""verify_instances - 验证 9 档命名实例的插值质量

检查:
  1. 各档墨量是否单调递增（插值异常会出现回落）
  2. 各档是否有 bbox 超界（>1000 或 <0 的异常）
  3. 各档字形数与 cmap 是否一致
  4. 相邻档墨量增幅是否均匀
"""
import sys, io
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
WGTS = [250, 300, 350, 400, 500, 600, 700, 800, 900]
NAMES = ['ExtraLight','Light','Normal','Regular','Medium','SemiBold','Bold','ExtraBold','Heavy']
CH = '永国字体设计的一是不了在人有我他这中大来上'


def measure(wght):
    f = TTFont(VF)
    inst = instantiateVariableFont(f, {'wght': wght}, inplace=False,
                               updateFontNames=False)
    f.close()
    gs = inst.getGlyphSet(); cm = inst.getBestCmap()
    areas, overs = [], []
    for ch in CH:
        gn = cm.get(ord(ch))
        if not gn:
            continue
        ap = AreaPen(gs); bp = BoundsPen(gs)
        try:
            gs[gn].draw(ap); gs[gn].draw(bp)
        except Exception:
            continue
        areas.append(abs(ap.value))
        if bp.bounds:
            x0, y0, x1, y1 = bp.bounds
            if x0 < -5 or y0 < -300 or x1 > 1005 or y1 > 1100:
                overs.append((ch, round(x0), round(y0), round(x1), round(y1)))
    n = len(inst.getGlyphOrder()); nc = len(cm)
    inst.close()
    return np.mean(areas), n, nc, overs


def main():
    print('%-10s %-6s %-12s %-8s %-8s %s' % ('实例','wght','墨面积均值','glyphs','cmap','超界'))
    prev = None
    rows = []
    for w, nm in zip(WGTS, NAMES):
        a, n, nc, overs = measure(w)
        flag = ''
        if prev is not None and a <= prev:
            flag = '  <<< 非递增!'
        print('%-10s %-6d %-12.0f %-8d %-8d %s%s' % (nm, w, a, n, nc,
              len(overs) if overs else '0', flag))
        rows.append((w, a))
        prev = a
    print()
    print('=== 相邻档增幅 ===')
    for i in range(1, len(rows)):
        w0, a0 = rows[i-1]; w1, a1 = rows[i]
        d = (a1 - a0) / a0 * 100
        per = d / (w1 - w0) * 100
        print('  %d->%d: 墨面积 %+.1f%%  每百单位 %+.2f%%' % (w0, w1, d, per))


main()