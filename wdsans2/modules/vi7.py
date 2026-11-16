#!/usr/bin/env python3
"""vi7 - 检查康熙部首映射是否与参考一致"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

FONTS = [('我们', '/workspace/static/wdsans/WDesignSans-VF.otf'),
         ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
         ('OPPO', '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
         ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf')]

# U+2F00-2FD5 康熙部首, U+4E00- 统一汉字
print('=== 抽查 CJK 的 glyph 名（是否用康熙部首名）===')
CH = '一丨丶人儿入八几刀力十口日月木水火土王'
print('%-4s %-14s %-14s %-14s %-14s' % ('字','我们','SHS','OPPO','HOS'))
for ch in CH:
    row = [ch]
    for lbl, p in FONTS:
        f = TTFont(p, lazy=True)
        cm = f.getBestCmap()
        gn = cm.get(ord(ch))
        row.append(gn if gn else '-')
        f.close()
    print('%-4s %-14s %-14s %-14s %-14s' % tuple(row))

print()
print('=== 康熙部首区 U+2F00-2FD5 覆盖 ===')
for lbl, p in FONTS:
    f = TTFont(p, lazy=True); cm = f.getBestCmap()
    n = sum(1 for cp in cm if 0x2F00 <= cp <= 0x2FD5)
    print('  %-5s %d 个' % (lbl, n))
    f.close()