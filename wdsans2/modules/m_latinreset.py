#!/usr/bin/env python3
"""m_latinreset - 撤销 m_latinmat 的 0.943 横向缩放，恢复 Mona 原宽

用户反馈: 「拉丁字体怎么窄了这么多？」「和MonaSans比宽了很多啊」

实测根因（400 档，墨宽）:
  字   我们      Mona@400   墨宽比
  H    550       583        0.944
  A    597       636        0.939
  M    687       728        0.943
  W    858       910        0.943
  n    412       435        0.947
  0    453       483        0.937

所有拉丁字形都只剩 Mona 原宽的 94.3%（= m_latinmat 的 SCALE）。

而 advance 却是 Mona 原值（H=764 A=697 M=894 W=994）：
  -> 轮廓被压窄 5.7% 但 advance 未变
  -> 字形变窄 + 字距变宽 -> 混排显得松散

m_latinmat 的历史理由: 「拉丁竖干比 CJK 粗 5.7%」，
但那是对 SHS 拉丁的测量；我们从 Mona 注入的字形本身就协调，
不该再压窄。

修法: 对所有拉丁字形轮廓做 1/0.943 的反向横向缩放（绕字形中心）。
     段数与操作符不变 -> 三档天然一致。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.transformPen import TransformPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R16')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R18')
FN = {'250': 'master-ExtraLight-250.otf',
      '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
SCALE = 0.943
K = 1.0 / SCALE      # 1.0604 反向缩放

LATIN_RANGES = [
    (0x0020, 0x007E), (0x00A0, 0x024F), (0x0250, 0x02AF),
    (0x1E00, 0x1EFF), (0x2000, 0x206F), (0x20A0, 0x20CF),
]


def in_latin(cp):
    for lo, hi in LATIN_RANGES:
        if lo <= cp <= hi:
            return True
    return False


def scale_x(C, k):
    """绕轮廓自身中心做 x 缩放"""
    if not C:
        return C
    xs = []
    for c in C:
        xs.append(c['start'][0])
        for s in c['segs']:
            if s[0] == 'QM':
                for p in s[1]:
                    xs.append(p[0])
            elif s[0] == 'C':
                xs.extend([s[1][0], s[2][0], s[3][0]])
            elif s[0] == 'Q':
                xs.extend([s[1][0], s[2][0]])
            else:
                xs.append(s[1][0])
    cx = (min(xs) + max(xs)) / 2.0

    def tx(x):
        return cx + (x - cx) * k

    NEW = []
    for c in C:
        segs = []
        for s in c['segs']:
            if s[0] == 'L':
                segs.append(['L', (tx(s[1][0]), s[1][1])])
            elif s[0] == 'C':
                segs.append(['C', (tx(s[1][0]), s[1][1]), (tx(s[2][0]), s[2][1]),
                             (tx(s[3][0]), s[3][1])])
            elif s[0] == 'Q':
                segs.append(['Q', (tx(s[1][0]), s[1][1]), (tx(s[2][0]), s[2][1])])
            elif s[0] == 'QM':
                segs.append(['QM', [(tx(p[0]), p[1]) for p in s[1]]])
            else:
                segs.append(list(s))
        NEW.append({'start': (tx(c['start'][0]), c['start'][1]), 'segs': segs})
    return NEW


def main():
    os.makedirs(OUTD, exist_ok=True)
    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        cm = f.getBestCmap()
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        n = 0
        for cp, gn in cm.items():
            if not in_latin(cp):
                continue
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                continue
            C = contours_from_pen(rp.value)
            if not C:
                continue
            NEW = scale_x(C, K)
            old = csT[gn]
            try:
                csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
                n += 1
            except Exception:
                continue
        print('  %s: 恢复 %d 个拉丁字形原宽' % (tag, n), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


if __name__ == "__main__":
    main()
