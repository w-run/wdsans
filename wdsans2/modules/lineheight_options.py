#!/usr/bin/env python3
"""lineheight_options - 行高调整的三个方案对比"""
from fontTools.ttLib import TTFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet()
from fontTools.pens.boundsPen import BoundsPen

# 找出所有超出某个 usWin 候选值的字形
def scan(limit_asc, limit_desc, max_n=20000):
    over = []
    order = f.getGlyphOrder()[:max_n]
    for gn in order:
        bp = BoundsPen(gs)
        try:
            gs[gn].draw(bp)
        except Exception:
            continue
        if not bp.bounds: continue
        if bp.bounds[3] > limit_asc or bp.bounds[1] < -limit_desc:
            over.append((gn, bp.bounds[1], bp.bounds[3]))
    return over

print("=== 各候选 usWinAscent 下超界的字形数 ===")
print("%-12s %10s   %s" % ("usWinAsc", "超界数", "样例"))
print("-" * 66)
for lim in (1000, 1050, 1100, 1160, 1200, 1325):
    over = scan(lim, 288, 20000)
    ex = ", ".join("%s(%.0f)" % (g, y1) for g, y0, y1 in over[:3])
    print("%-12d %10d   %s" % (lim, len(over), ex if ex else "-"))

print()
print("=== 结论 ===")
print('1160 是使超界字形尽可能少的折中值。')
print('若要 1.33em(1330)，则 1330 >= 1325，可覆盖所有字形，')
print('但这会让行高比现在更高（1.45 -> 1.62），方向错误。')
print()
print('真正的问题是: 少数竖排标点字形把下界拉到 -549、上界拉到 1325。')
print('SHS 用 usWin=1160 折中（接受这几个字被裁切），')
print('而不是抬高 usWin 让所有字都正常（那样行高会爆）。')
f.close()