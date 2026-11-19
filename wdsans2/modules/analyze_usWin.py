#!/usr/bin/env python3
"""analyze_usWin - 分析 usWinAscent=1160 的来源与合理性"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)

print("=== 1. CJK 字形的实际上下界 ===")
cm = f.getBestCmap(); gs = f.getGlyphSet()
from fontTools.pens.boundsPen import BoundsPen
import numpy as np

# 抽样 CJK 的 y 范围
ymin_all, ymax_all = [], []
sample = [c for c in cm if 0x4E00 <= c <= 0x9FFF][:3000]
for cp in sample:
    gn = cm[cp]
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if bp.bounds:
        ymin_all.append(bp.bounds[1]); ymax_all.append(bp.bounds[3])
if ymax_all:
    print("  3000 字抽样: ymin=%.0f  ymax=%.0f" % (min(ymin_all), max(ymax_all)))
    print("  -> CJK 墨迹最高 %.0f，而 usWinAscent=1160" % max(ymax_all))
    print("  -> 富余 %.0f 单位（留给注音/上标）" % (1160 - max(ymax_all)))

print()
print("=== 2. 所有 glyph 的极端 y 值 ===")
order = f.getGlyphOrder()
gmin, gmax = 1e9, -1e9
extreme_hi, extreme_lo = None, None
for gn in order[:8000]:
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > gmax:
        gmax = bp.bounds[3]; extreme_hi = gn
    if bp.bounds[1] < gmin:
        gmin = bp.bounds[1]; extreme_lo = gn
print("  最高: %.0f (%s)" % (gmax, extreme_hi))
print("  最低: %.0f (%s)" % (gmin, extreme_lo))
print("  usWinAscent=1160 / usWinDescent=288")
if gmax <= 1160 and gmin >= -288:
    print("  -> 当前设置能完整容纳所有字形（无裁切）")
else:
    print("  -> !! 有字形超出 usWin 范围")

print()
print("=== 3. 若改成 1.33em 会怎样 ===")
print("  usWin 需覆盖所有字形。若最高 %.0f，则 usWinAscent 至少要 %.0f" % (gmax, gmax))
print("  但 SHS 原版就是 1160 -> 这是上游设计，改了会与基座不一致")
f.close()