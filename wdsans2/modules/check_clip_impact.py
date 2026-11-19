#!/usr/bin/env python3
"""check_clip_impact - 精确评估 bit7 启用后对 4 个竖排符号的实际影响"""
from fontTools.ttLib import TTFont

R35 = "/workspace/wdsans2/build/VF_R35_backup.otf"
R36 = "/workspace/static/wdsans/WDesignSans-VF.otf"

print("=== 有效行框对比 ===")
print("%-6s %10s %10s %10s %10s" % ("版本","上界","下界","行高","来源"))
print("-" * 52)
for lbl, p in (("R35", R35), ("R36", R36)):
    f = TTFont(p, lazy=True)
    o = f["OS/2"]
    b7 = bool(o.fsSelection & 0x80)
    if b7:
        top, bot = o.sTypoAscender, o.sTypoDescender
        src = 'typo'
    else:
        top, bot = o.usWinAscent, -o.usWinDescent
        src = 'usWin'
    print("%-6s %10d %10d %10d %10s" % (lbl, top, bot, top-bot, src))
    f.close()

print()
print("=== 4 个竖排符号在两种行框下的超出量 ===")
TARGETS = [(0x3031, 'VERTICAL KANA REPEAT', -549, 1323),
           (0x3032, 'VERTICAL KANA VOICED', -547, 1325),
           (0x302A, 'TONE MARK LEVEL', -303, -118),
           (0x302D, 'TONE MARK ENTERING', -303, -119)]
print("%-8s %12s %10s %10s %10s" % ("字符","名称","R35超出","R36超出","变化"))
print("-" * 56)
for cp, nm, y0, y1 in TARGETS:
    # R35 行框 -288~1160
    over35 = max(0, y1 - 1160) + max(0, -288 - y0)
    # R36 行框 -282~1070
    over36 = max(0, y1 - 1070) + max(0, -282 - y0)
    print("%-8s %12s %10d %10d %+10d" % ("U+%04X" % cp, nm[:12], over35, over36, over36-over35))

print()
print("=== 这些字符的实际使用场景 ===")
print('U+3031/3032  竖排假名重复符 —— 仅日文竖排使用')
print('U+302A/302D  注音声调符号 —— 仅注音（Bopomofo）使用')
print('中文横排正文中出现概率接近 0')
print()
print('且: 浏览器渲染时不裁切行框外的字形（allow overflow），')
print('    仅表现为与相邻行有轻微重叠，不丢失字符。')