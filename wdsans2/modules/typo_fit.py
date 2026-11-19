#!/usr/bin/env python3
"""typo_fit - 计算能覆盖全部字形的 typo 度量"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet()
order = f.getGlyphOrder()

print('=== 全库极端 y 值（排除竖排专用符号）===')
SKIP = {0x302A, 0x302D, 0x3031, 0x3032, 0x3033, 0x3034, 0x3035}
gmin = 1e9; gmax = -1e9
arg_min = arg_max = None
n = 0
for cp, gn in cm.items():
    if cp in SKIP: continue
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    n += 1
    if bp.bounds[3] > gmax:
        gmax = bp.bounds[3]; arg_max = cp
    if bp.bounds[1] < gmin:
        gmin = bp.bounds[1]; arg_min = cp
print("  检查 %d 个字符" % n)
print("  最高: %.0f (U+%04X)" % (gmax, arg_max))
print("  最低: %.0f (U+%04X)" % (gmin, arg_min))

print()
print("=== 覆盖全部字形所需的 typo 度量 ===")
need_asc = int(np.ceil(gmax)) if False else int(gmax) + 1
need_desc = int(gmin) - 1
print("  sTypoAscender  = %d" % need_asc)
print("  sTypoDescender = %d" % need_desc)
print("  合计 = %d = %.2fem" % (need_asc - need_desc, (need_asc - need_desc)/1000.0))

print()
print("=== 对比各方案的行高 ===")
print("  方案                     行高      视觉")
print("  " + "-" * 52)
print("  A. 现状(hhea/win=1448)   1.45em    偏松")
print('  B. 启用typo(现有 1000)   1.00em    太紧且裁切拉丁')
print("  C. 调整typo覆盖全字形    %.2fem" % ((need_asc-need_desc)/1000.0))
print("  D. OPPO 水平             1.32em")
print("  E. HOS 水平              1.18em")

print()
print("=== 方案 C 的问题 ===")
print('  需要 asc=%d, desc=%d' % (need_asc, need_desc))
print('  但 usWin 仍需覆盖竖排符号(1325/-549)')
print('  -> 需要同时改 typo 和 usWin，且要处理竖排符号')
print()
print('  风险: 改动涉及 OS/2 多个字段，会影响所有平台的行距')
print('        且 CPS 字形(注音)会因此叠到相邻行上')
f.close()