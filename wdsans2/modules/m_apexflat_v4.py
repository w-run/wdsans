#!/usr/bin/env python3
"""m_apexflat_v4 - 顶点平顶（最终版，仅单档静态字体）

背景:
  多档 VF 下不可行（pathops 三档拓扑不一致 99.7%）。
  单档静态字体无插值约束，可以实现。

HOS/OPPO 的做法(今):
  HOS:  qCurveTo(464,839) -> lineTo(540,839)   平顶宽 76
  OPPO: qCurveTo(460,824) -> lineTo(528,824)   平顶宽 68
  我们: 两个独立尖点，无平顶

实现:
  1. 找顶部 60 单位内的两个独立轮廓
  2. pathops.union 合并
  3. pathops.difference(merged.contours, cutter.contours, out.getPen()) 减掉顶部矩形

🔴 关键 API 坑:
  - path.contours 是**生成器**，必须 list() 转换
  - difference(subject_contours, clip_contours, outpen) 三个位置参数，
    前两个要传**轮廓列表**而不是 Path 对象
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R25')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/static_apex4')
FN = 'master-Regular-400.otf'

APEX_WIN = 55
FLAT_DEPTH = 20


def c2p(c):
    p = pathops.Path(); pen = p.getPen()
    pen.moveTo(c['start'])
    for s in c['segs']:
        if s[0] == 'L':
            pen.lineTo(s[1])
        elif s[0] == 'C':
            pen.curveTo(s[1], s[2], s[3])
        elif s[0] == 'Q':
            pen.qCurveTo(s[1], s[2])
        elif s[0] == 'QM':
            pen.qCurveTo(*s[1])
    pen.closePath()
    return p


def ymax_of(c):
    ys = [c['start'][1]]
    for s in c['segs']:
        if s[0] == 'QM':
            ys.extend(p[1] for p in s[1])
        elif s[0] == 'C':
            ys.extend([s[1][1], s[2][1], s[3][1]])
        elif s[0] == 'Q':
            ys.extend([s[1][1], s[2][1]])
        else:
            ys.append(s[1][1])
    return max(ys)


def find_apex(C):
    if not C or len(C) < 2:
        return None
    tops = [(ci, ymax_of(c)) for ci, c in enumerate(C)]
    gmax = max(t[1] for t in tops)
    near = [t for t in tops if t[1] > gmax - APEX_WIN]
    if len(near) != 2:
        return None
    return near[0][0], near[1][0], gmax


def flatten_apex(C, ci_a, ci_b, gmax):
    pa = c2p(C[ci_a]); pb = c2p(C[ci_b])
    merged = pathops.Path()
    pathops.union([pa, pb], merged.getPen())

    # 全字形 bbox 用于切刀宽度
    xs = []; ys = []
    for c in C:
        xs.append(c['start'][0]); ys.append(c['start'][1])
        for s in c['segs']:
            if s[0] == 'QM':
                for pt in s[1]:
                    xs.append(pt[0]); ys.append(pt[1])
            elif s[0] == 'C':
                xs.extend([s[1][0], s[2][0], s[3][0]])
                ys.extend([s[1][1], s[2][1], s[3][1]])
            elif s[0] == 'Q':
                xs.extend([s[1][0], s[2][0]])
                ys.extend([s[1][1], s[2][1]])
            else:
                xs.append(s[1][0]); ys.append(s[1][1])
    x0 = min(xs) - 100; x1 = max(xs) + 100
    ycut = gmax - FLAT_DEPTH

    cutter = pathops.Path()
    cp = cutter.getPen()
    cp.moveTo((x0, ycut)); cp.lineTo((x1, ycut))
    cp.lineTo((x1, gmax + 200)); cp.lineTo((x0, gmax + 200))
    cp.closePath()

    out = pathops.Path()
    pathops.difference(list(merged.contours), list(cutter.contours), out.getPen())

    rp = RecordingPen()
    out.draw(rp)
    return contours_from_pen(rp.value)


def main():
    os.makedirs(OUTD, exist_ok=True)
    f = TTFont(SRC + '/' + FN)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    cff2 = f['CFF2'].cff
    td = cff2[cff2.fontNames[0]]
    csT = td.CharStrings
    cjk = [(cp, gn) for cp, gn in cm.items() if 0x4E00 <= cp <= 0x9FFF]
    print('扫描 %d 个 CJK' % len(cjk), flush=True)

    done = 0; skip = 0; samples = []
    for cp, gn in cjk:
        rp = RecordingPen()
        try:
            gs[gn].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        pair = find_apex(C)
        if not pair:
            continue
        ci_a, ci_b, gmax = pair
        try:
            Cm = flatten_apex(C, ci_a, ci_b, gmax)
        except Exception:
            skip += 1
            continue
        if not Cm:
            skip += 1
            continue
        Cfinal = [c for i, c in enumerate(C) if i not in (ci_a, ci_b)] + Cm
        old = csT[gn]
        try:
            csT[gn] = make_charstring(Cfinal, old.private, old.globalSubrs)
            done += 1
            if len(samples) < 14:
                samples.append(chr(cp))
        except Exception:
            skip += 1

    print('截平 %d 字, 跳过 %d' % (done, skip), flush=True)
    print('样例: %s' % ''.join(samples), flush=True)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    f.save(OUTD + '/' + FN)
    f.close()
    print('保存 -> %s/%s' % (OUTD, FN))


main()