#!/usr/bin/env python3
"""eval_options - U+2022 三个可选方案的代价评估"""
from fontTools.ttLib import TTFont
VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
cm = f.getBestCmap()

print("=== 方案 A: 覆写一个未引用的槽位（11,724 个可选）===")
print('  + 不改 numGlyphs，无上限问题')
print('  + 只改 1 个 glyph，其他零影响')
print('  - 会丢失该槽位原有轮廓（虽未被引用）')
print('  - 若未来某特性需要它，会拿到错误的字形')

print("=== 方案 B: 让 U+2022 继续共用 periodcentered ===")
print('  + 零风险')
print('  - 项目符号仍偏小（118 vs 参考 229）')
print('  - 但这是 SHS 原版设计（SHS 也共用 cid01649）')

print("=== 方案 C: 用 25CF(●) 缩放后作为 bullet ===")
print('  需要新槽位或覆写 -> 回到方案 A 的问题')
print('  且 ● 原本 743x747，缩放 0.31 后描边质量可能下降')

print()
print("=== 关键事实: SHS 原版怎么做的？ ===")
rf = TTFont("/workspace/wdsans/ref/shs/shs-400.otf", lazy=True)
rcm = rf.getBestCmap()
for cp in (0x00B7, 0x2022, 0x2027, 0x30FB):
    gn = rcm.get(cp, "无")
    print("  U+%04X -> %s" % (cp, gn))
rf.close()

print()
print("结论: SHS 自己也是四个码位共用一个字形（cid01649）。")
print("      我们的 118x126 就是 SHS 的设计（只是换了三次曲线）。")
print("      参考字体 OPPO/HOS 拆分是因为它们自己重新设计了标点。")
f.close()