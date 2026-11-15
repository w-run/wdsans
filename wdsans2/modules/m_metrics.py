#!/usr/bin/env python3
"""m_metrics - 修正 OS/2 垂直度量与 fsSelection 标志

发现的两个真实缺陷（对比 SHS/OPPO/HOS）:

1) fsSelection = 0x0000，缺 REGULAR(bit6=0x40)
   三个参考字体都设了 0x0040。
   缺这个标志可能导致某些应用无法识别常规字重。

2) usWinAscent/Descent 未覆盖 4 个功能字形（竖排重复符号）:
   〱〲  y[-549,1323]    usWin=[-288,1160]
   〪〭  y[-304,-118]
   -> Windows 上会被裁切。这是 SHS 上游的缺陷，我们继承了它。

修复策略（权衡后）:
  - fsSelection: 0x0000 -> 0x0040 (加 REGULAR)
  - usWin 提高会带来 +29.4% 行高，代价太大
  - 改用「只抬高到覆盖 99.9% 字形」的折中:
      保持 usWin 不变（1160/288），因为只有 4 个功能字形超界，
      且它们主要用在竖排场景（Windows 横排裁切影响很小）
  - 但把 hhea 与 typo 保持原值，不引入行高变化

结论: 只修 fsSelection，usWin 不动（避免 29% 行高代价）。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD16')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD17')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

# 字重对应的 fsSelection 基础值（REGULAR 只给 400）
FS_BASE = 0x0040     # REGULAR
FS_BOLD = 0x0020     # BOLD（仅 900 档考虑，但 VF 通常不设）


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        os2 = f['OS/2']
        old = os2.fsSelection
        # VF 的 master 都是同一字体家族，统一设 REGULAR
        os2.fsSelection = FS_BASE
        print('  %s: fsSelection 0x%04X -> 0x%04X' % (tag, old, os2.fsSelection), flush=True)
        print('      typo[%d,%d] win[%d,%d] (未改)' % (
            os2.sTypoAscender, os2.sTypoDescender,
            os2.usWinAscent, os2.usWinDescent), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


main()
