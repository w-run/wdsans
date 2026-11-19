#!/usr/bin/env python3
"""hhea_fit - 评估直接压低 hhea/usWin 是否可行"""
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap(); gs = f.getGlyphSet()

# 排除竖排专用符号后的极端值
SKIP = {0x302A, 0x302D, 0x3031, 0x3032, 0x3033, 0x3034, 0x3035}
gmin = 1e9; gmax = -1e9
arg_min = arg_max = None
for cp, gn in cm.items():
    if cp in SKIP: continue
    bp = BoundsPen(gs)
    try:
        gs[gn].draw(bp)
    except Exception:
        continue
    if not bp.bounds: continue
    if bp.bounds[3] > gmax: gmax = bp.bounds[3]; arg_max = cp
    if bp.bounds[1] < gmin: gmin = bp.bounds[1]; arg_min = cp

print("=== 若要 hhea = 1.35em (1352) ===")
print("  需 cover y 范围: %.0f ~ %.0f (共 %.0f)" % (gmin, gmax, gmax-gmin))
print("  取 asc=%.0f desc=%.0f -> 合计 %.0f = %.2fem" % (gmax, gmin, gmax-gmin, (gmax-gmin)/1000.0))

print()
print("=== 与 OPPO/HOS 的行高对比 ===")
print("  OPPO: hhea asc=1000 desc=-319 -> 1319 = 1.32em")
print("  HOS : hhea asc= 928 desc=-244 -> 1172 = 1.17em")
print('  我们(现): asc=1160 desc=-288 -> 1448 = 1.45em')
print("  我们(新): asc=%.0f desc=%.0f -> %.0f = %.2fem" % (gmax, gmin, gmax-gmin, (gmax-gmin)/1000.0))

print()
print("=== 🔴 但这样会让出界字形被裁切 ===")
print('  排除的 7 个竖排符号: 上界 1325 下界 -549')
print('  改后 usWin = %d，这 7 个字会被裁切' % (gmax - gmin))
print()
print('  SHS 的选择是: 保留 1160/288 让这 7 个字勉强可见')
print('  代价是全局行高偏大 10%')

print()
print("=== 三个选项的最终权衡 ===")
print("  1. 保持现状 1.45em")
print("     + 零风险，与 SHS 一致，所有字形完整")
print("     - 行距偏松 10%（但 CSS line-height 可覆盖）")
print()
print("  2. 压到 1.35em（hhea+usWin 同改）")
print("     + 与 OPPO 接近")
print("     - 7 个竖排符号被裁切")
print("     - 与 SHS 基座不一致")
print()
print("  3. 启用 USE_TYPO_METRICS（需 OS/2 v3->v4）")
print("     + 同时保留 usWin 大值（竖排符号不裁）")
print('     + typo 可独立设成 1.35em，行高正确')
print("     - 需升级 OS/2 版本（结构变更）")
print("     - 三家参考字体都没这么做，属于自创")

f.close()