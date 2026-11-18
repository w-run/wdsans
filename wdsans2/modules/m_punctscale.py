#!/usr/bin/env python3
"""m_punctscale - 中文句读类标点缩小，对齐 OPPO/HOS

量化发现（2026-11-16，墨宽/墨高，400 档）:
  字   我们      OPPO     HOS     vsOPPO   vsHOS   类型
  。  304x304  270x274 270x275  +11.8%  +11.6%  句号
  、  289x280  242x226 236x228  +21.5%  +22.6%  顿号
  ，  194x341  146x236 129x259  +41.4%  +35.6%  逗号
  ：  150x641  120x529 113x542  +21.4%  +18.9%  冒号
  ；  194x797  157x657 129x688  +21.4%  +17.2%  分号
  ！  128x752  122x735 113x770   +2.4%   -2.0%  感叹号(正常)
  ？  427x766  414x744 424x781   +3.0%   -1.3%  问号(正常)

规律: 句读类（。、，：；）偏大 11~41%，感叹/问号正常。
SHS 原版就是这么大（已逐阶段溯源确认），是风格取向差异。
项目目标是贴近 OPPO/HOS -> 缩小句读类标点。

修法: 对命中字形所有轮廓点绕「字形中心」等比缩放 k。
段数/操作符不变 -> 三档天然一致。
目标: 缩放到 OPPO 与 HOS 的对角线均值。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R22')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_R23')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}

# 目标缩放系数（按对角线，vs OPPO/HOS 均值）
#   1/(1.117) = 0.895 ; 1/(1.220) = 0.820 ; 1/(1.385) = 0.722
#   1/(1.201) = 0.833 ; 1/(1.193) = 0.838
# 取各字独立系数，但三档必须一致
SCALE = {
    0x3002: 0.895,   # 。
    0x3001: 0.820,   # 、
    0xFF0C: 0.722,   # ，
    0xFF1A: 0.833,   # ：
    0xFF1B: 0.838,   # ；
}


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def scale_contours(C, k):
    """绕所有点的 bbox 中心等比缩放 x 与 y"""
    xs, ys = [], []
    for c in C:
        xs.append(c['start'][0]); ys.append(c['start'][1])
        for s in c['segs']:
            if s[0] == 'QM':
                for p in s[1]:
                    xs.append(p[0]); ys.append(p[1])
            elif s[0] == 'C':
                xs.extend([s[1][0], s[2][0], s[3][0]])
                ys.extend([s[1][1], s[2][1], s[3][1]])
            elif s[0] == 'Q':
                xs.extend([s[1][0], s[2][0]])
                ys.extend([s[1][1], s[2][1]])
            else:
                xs.append(s[1][0]); ys.append(s[1][1])
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0

    def tx(x):
        return cx + (x - cx) * k

    def ty(y):
        return cy + (y - cy) * k

    NEW = []
    for c in C:
        segs = []
        for s in c['segs']:
            if s[0] == 'L':
                segs.append(['L', (tx(s[1][0]), ty(s[1][1]))])
            elif s[0] == 'C':
                segs.append(['C', (tx(s[1][0]), ty(s[1][1])),
                             (tx(s[2][0]), ty(s[2][1])),
                             (tx(s[3][0]), ty(s[3][1]))])
            elif s[0] == 'Q':
                segs.append(['Q', (tx(s[1][0]), ty(s[1][1])),
                             (tx(s[2][0]), ty(s[2][1]))])
            elif s[0] == 'QM':
                segs.append(['QM', [(tx(p[0]), ty(p[1])) for p in s[1]]])
            else:
                segs.append(list(s))
        NEW.append({'start': (tx(c['start'][0]), ty(c['start'][1])), 'segs': segs})
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
        for cp, k in SCALE.items():
            gn = cm.get(cp)
            if not gn:
                continue
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                continue
            C = contours_from_pen(rp.value)
            if not C:
                continue
            NEW = scale_contours(C, k)
            old = csT[gn]
            try:
                csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
                n += 1
            except Exception as e:
                print('    %s 失败: %s' % (gn, e), flush=True)
        print('  %s: 缩放 %d 个标点' % (tag, n), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()
    print('完成 -> %s' % OUTD)


if __name__ == "__main__":
    main()
