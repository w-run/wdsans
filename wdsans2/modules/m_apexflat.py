#!/usr/bin/env python3
"""m_apexflat - 顶点平顶（仅单档静态字体）

判据（关键）:
  找「顶部 70 单位内的两个轮廓」，且两个轮廓的「顶部墨宽」都 < 40。
  顶部墨宽 = 轮廓顶部 3% 高度带内的 x 跨度。
  尖点 -> 0~1；横画 -> 700+；竖笔端面 -> 70~80。

实测区分:
  今  c2 顶宽 1   c3 顶宽 0    <- 双尖点，命中
  合  c3 顶宽 0   c4 顶宽 0    <- 双尖点，命中
  甲  c0 顶宽 79  c1 顶宽 751  <- 竖笔端面+横画，跳过
  田  c2 顶宽 810 c3 顶宽 76   <- 横画+竖笔端面，跳过

HOS/OPPO 参考值(今): 平顶宽 HOS 76 / OPPO 68
"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
import pathops
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_R25')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/static_apex')
FN = 'master-Regular-400.otf'

APEX_WIN = 70
FLAT_DEPTH = 28
MAX_TOPW = 40      # 顶部墨宽上限（区分尖点与横画/竖笔端面）


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


def flat_np(c, n=16):
    pts = [np.array(c['start'], float)]
    prev = pts[0]
    for s in c['segs']:
        if s[0] == 'L':
            p = np.array(s[1], float); pts.append(p); prev = p
        elif s[0] == 'C':
            P = [prev, np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)]
            for i in range(1, n+1):
                pts.append(bezierTools.splitCubicAtT(*P, i/n)[0][-1])
            prev = P[3]
        elif s[0] == 'Q':
            P = [prev, np.array(s[1], float), np.array(s[2], float)]
            for i in range(1, n+1):
                pts.append(bezierTools.splitQuadraticAtT(*P, i/n)[0][-1])
            prev = P[2]
        elif s[0] == 'QM':
            for p in s[1]:
                pts.append(np.array(p, float))
            prev = pts[-1]
    return np.array(pts)


def info_of(c):
    Q = flat_np(c)
    ymax = Q[:, 1].max()
    h = ymax - Q[:, 1].min()
    band = Q[Q[:, 1] > ymax - max(h * 0.03, 5)]
    topw = (band[:, 0].max() - band[:, 0].min()) if len(band) > 1 else 0
    return ymax, topw, Q


def find_apex(C):
    if not C or len(C) < 2:
        return None
    infos = [(ci,) + info_of(c)[:2] for ci, c in enumerate(C)]
    gmax = max(i[1] for i in infos)
    near = [i for i in infos if i[1] > gmax - APEX_WIN]
    if len(near) != 2:
        return None
    # 两个都必须是尖点（顶宽 < MAX_TOPW）
    if any(i[2] > MAX_TOPW for i in near):
        return None
    return near[0][0], near[1][0], gmax


def flatten_apex(C, ci_a, ci_b, gmax):
    pa = c2p(C[ci_a]); pb = c2p(C[ci_b])
    merged = pathops.Path()
    pathops.union([pa, pb], merged.getPen())

    allP = np.vstack([flat_np(c) for c in C])
    x0 = allP[:, 0].min() - 100; x1 = allP[:, 0].max() + 100
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