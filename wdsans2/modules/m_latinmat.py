#!/usr/bin/env python3
"""m_latinmat - 拉丁字形横向微缩，匹配 CJK 笔干重量

问题:
  Mona Sans 整合时未调横向比例，导致拉丁竖干比 CJK 竖干粗 18.7%，
  而 OPPO Sans 的对应比例是 13.9%。中英混排时拉丁显得偏粗。

判据（位图实测, 200px 字号）:
  CJK 竖干(口日田目)  15.5 px
  拉丁竖干(HnIEL)     18.4 px   比例 1.187
  OPPO 同样测量        14.8 / 16.8  比例 1.139
  -> 拉丁相对过粗 4.2% -> 横向缩放 0.960

修复:
  对拉丁字形所有轮廓点做 x 方向缩放（绕字形中心），advance width 不变。
  缩放不改变段数与操作符 -> 三档一致性自动满足。

为什么用横向缩放而不是换字重:
  Mona Sans 是 VF，换字重需要重建整个 10 阶段基座链；
  横向缩放只改最终 masters，代价小且风险低，4% 缩放在视觉上几乎不可察。
"""
import numpy as np

NAME = 'latinmat'
DESC = '拉丁字形横向微缩匹配 CJK 笔干'

SCALE = 0.943      # 横向缩放系数（按 OPPO 比例 1.136 校准）

# 拉丁字形码位范围（含 ASCII / Latin-1 / Latin Extended）
LATIN_RANGES = [
    (0x0020, 0x007E),   # Basic Latin
    (0x00A0, 0x024F),   # Latin-1 Supplement + Latin Extended-A/B
    (0x0250, 0x02AF),   # IPA
    (0x1E00, 0x1EFF),   # Latin Extended Additional
    (0x2000, 0x206F),   # General Punctuation
    (0x20A0, 0x20CF),   # Currency Symbols
]


def is_latin(cp):
    for lo, hi in LATIN_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def find(C, sw):
    """不做逐字检测 —— 由调用方按码位过滤。返回占位。"""
    return []


def scale_contours(C, k=SCALE):
    """把轮廓所有点沿 x 绕字形中心缩放 k 倍"""
    # 求包围盒中心
    allx = []
    for c in C:
        allx.append(c['start'][0])
        for s in c['segs']:
            if s[0] == 'L':
                allx.append(s[1][0])
            elif s[0] == 'C':
                allx.extend([s[1][0], s[2][0], s[3][0]])
            elif s[0] == 'Q':
                allx.extend([s[1][0], s[2][0]])
            elif s[0] == 'QM':
                allx.extend([p[0] for p in s[1]])
    if not allx:
        return C
    cx = (min(allx) + max(allx)) / 2.0

    def sx(x):
        return cx + (x - cx) * k

    NEW = []
    for c in C:
        start = (sx(c['start'][0]), c['start'][1])
        segs = []
        for s in c['segs']:
            if s[0] == 'L':
                segs.append(['L', (sx(s[1][0]), s[1][1])])
            elif s[0] == 'C':
                segs.append(['C', (sx(s[1][0]), s[1][1]),
                             (sx(s[2][0]), s[2][1]), (sx(s[3][0]), s[3][1])])
            elif s[0] == 'Q':
                segs.append(['Q', (sx(s[1][0]), s[1][1]), (sx(s[2][0]), s[2][1])])
            elif s[0] == 'QM':
                segs.append(['QM', [(sx(p[0]), p[1]) for p in s[1]]])
            else:
                segs.append(list(s))
        NEW.append({'start': start, 'segs': segs})
    return NEW


def apply(C, hits):
    return scale_contours(C, SCALE)
