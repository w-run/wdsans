#!/usr/bin/env python3
"""m_apexflat_v3 - 顶点平顶 v3

v2 失败原因: pathops.difference 签名是
  difference(subject_contours, clip_contours, outpen, ...)
  需要 3 个位置参数，我只传了 2 个。

HOS 的做法(今): qCurveTo(464,839) -> lineTo(540,839)
  = 顶部有 76 单位宽的水平线。

实现: 合并两个顶部轮廓 -> 用 difference 减掉顶部矩形 -> 得到平顶
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R25')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/static_apex3')
FN = 'master-Regular-400.otf'

APEX_WIN = 60
FLAT_DEPTH = 22


def find_apex(C):
    if not C or len(C) < 2:
        return None
    tops = []
    for ci, c in enumerate(C):
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
        tops.append((ci, max(ys)))
    gmax = max(t[1] for t in tops)
    near = [t for t in tops if t[1] > gmax - APEX_WIN]
    if len(near) != 2:
        return None
    return near[0][0], near[1][0], gmax


def contour_to_path(c):
    p = pathops.Path()
    pen = p.getPen()
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


def flatten_apex(C, ci_a, ci_b, gmax):
    # 1) 合并两轮廓
    pa = contour_to_path(C[ci_a]); pb = contour_to_path(C[ci_b])
    merged = pathops.Path()
    pathops.union([pa, pb], merged.getPen())

    # 2) 顶部切刀
    allx = []; ally = []
    for c in C:
        allx.append(c['start'][0]); ally.append(c['start'][1])
        for s in c['segs']:
            if s[0] == 'QM':
                for pt in s[1]:
                    allx.append(pt[0]); ally.append(pt[1])
            elif s[0] == 'C':
                allx.extend([s[1][0], s[2][0], s[3][0]])
                ally.extend([s[1][1], s[2][1], s[3][1]])
            elif s[0] == 'Q':
                allx.extend([s[1][0], s[2][0]])
                ally.extend([s[1][1], s[2][1]])
            else:
                allx.append(s[1][0]); ally.append(s[1][1])
    x0 = min(allx) - 100; x1 = max(allx) + 100
    ycut = gmax - FLAT_DEPTH
    ytop = gmax + 200

    cutter = pathops.Path()
    cp = cutter.getPen()
    cp.moveTo((x0, ycut)); cp.lineTo((x1, ycut))
    cp.lineTo((x1, ytop)); cp.lineTo((x0, ytop))
    cp.closePath()

    # 3) difference(merged, cutter, outpen)  <- 3 个位置参数
    out = pathops.Path()
    pathops.difference(merged, cutter, out.getPen())

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
            if len(samples) < 12:
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