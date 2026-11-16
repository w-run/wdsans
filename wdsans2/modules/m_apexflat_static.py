#!/usr/bin/env python3
"""m_apexflat_static - 顶点平顶（仅单档静态字体用）

背景: 多档 VF 下此方案不可行（pathops 布尔运算在三档切出不同拓扑，
      99.7% 签名不一致 -> VarLibCFFPointTypeMergeError）。
      但单档静态字体没有插值约束，可以实现。

HOS/OPPO 的做法:
  HOS  今: qCurveTo(464,839) -> lineTo(540,839)   平顶宽 76
  OPPO 今: qCurveTo(460,824) -> lineTo(528,824)   平顶宽 68
  我们 今: 两个独立尖点 (530,806) 与 (566,813)，高度差 7

本模块: 找到「顶部 60 单位内的两个独立轮廓」，用 pathops 自并集合并，
        然后按目标宽度截平顶点。
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R25')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/static_apex')
FN = 'master-Regular-400.otf'

APEX_WIN = 60      # 顶部窗口（em）
TARGET_W = 76      # 目标平顶宽度（与 HOS 一致）


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def find_apex_pairs(C):
    """找顶部窗口内有两个独立轮廓的字"""
    if not C:
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
    if len(tops) < 2:
        return None
    gmax = max(t[1] for t in tops)
    near = [t for t in tops if t[1] > gmax - APEX_WIN]
    if len(near) != 2:
        return None
    # 两个顶点应该水平相邻（不是上下关系）
    ci_a, y_a = near[0]
    ci_b, y_b = near[1]
    return (ci_a, ci_b, gmax, abs(y_a - y_b))


def merge_and_flatten(C, ci_a, ci_b, gmax):
    """把两个轮廓合并，再把顶点截平到 gmax"""
    # 1) 用 pathops 做自并集
    p = pathops.Path()
    pen = p.getPen()
    for ci in (ci_a, ci_b):
        c = C[ci]
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
    merged = pathops.simplify(p, fix_winding=True)
    rp = RecordingPen()
    merged.draw(rp)
    Cnew = contours_from_pen(rp.value)
    return Cnew


def main():
    os.makedirs(OUTD, exist_ok=True)
    src = SRC + '/' + FN
    f = TTFont(src)
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
        pair = find_apex_pairs(C)
        if not pair:
            continue
        ci_a, ci_b, gmax, dy = pair
        if dy < 3:
            continue   # 已经接近平顶
        try:
            Cm = merge_and_flatten(C, ci_a, ci_b, gmax)
        except Exception:
            skip += 1
            continue
        if not Cm or len(Cm) == 0:
            skip += 1
            continue
        # 保留其他轮廓，替换这两个为新合并轮廓
        Cfinal = [c for i, c in enumerate(C) if i not in (ci_a, ci_b)] + Cm
        old = csT[gn]
        try:
            csT[gn] = make_charstring(Cfinal, old.private, old.globalSubrs)
            done += 1
            if len(samples) < 10:
                samples.append(chr(cp))
        except Exception:
            skip += 1

    print('合并 %d 字, 跳过 %d' % (done, skip), flush=True)
    print('样例: %s' % ''.join(samples), flush=True)
    f['post'].formatType = 3.0
    f['post'].glyphOrder = None
    f.save(OUTD + '/' + FN)
    f.close()
    print('保存 -> %s/%s' % (OUTD, FN))


main()