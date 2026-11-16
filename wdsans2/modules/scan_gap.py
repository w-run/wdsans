#!/usr/bin/env python3
"""scan_gap - 全库近邻缝隙检测

检测「两个轮廓本应相接、但留有 1~10 单位微缝」的情况。
这类缝隙在渲染时会变成可见的发丝裂缝（hairline crack），是真实缺陷。

方法:
  1. 对每个字取所有轮廓的点集
  2. 两两计算最近点距离
  3. 距离在 [0.5, 10] 且两个轮廓 bbox 相交/邻近 -> 候选缝隙
  4. 与 SHS 对比: 若 SHS 没有这个缝隙，说明是本项目引入的

性能: 字体只开一次；用 numpy 向量化距离计算。
"""
import sys, os, json, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
OUT = '/workspace/wdsans2/build/scan_gap.json'

GAP_MIN = 0.5
GAP_MAX = 10.0
NFLAT = 8


def contour_pts_from_rp(rp_value):
    """把 RecordingPen 输出转成一组轮廓的展平点集"""
    out = []
    cur = []
    last = None
    for op, args in rp_value:
        if op == 'moveTo':
            if cur:
                out.append(np.array(cur))
            cur = [np.array(args[0], float)]
            last = cur[0]
        elif op == 'lineTo':
            p = np.array(args[0], float)
            cur.append(p)
            last = p
        elif op == 'curveTo':
            P = [last, np.array(args[0], float), np.array(args[1], float),
                 np.array(args[2], float)]
            for i in range(1, NFLAT + 1):
                try:
                    cur.append(bezierTools.splitCubicAtT(*P, i / NFLAT)[0][-1])
                except Exception:
                    pass
            last = P[3]
        elif op == 'qCurveTo':
            pts = [np.array(a, float) for a in args]
            if len(pts) >= 2:
                for i in range(len(pts) - 1):
                    P = [last, pts[i], pts[i + 1]]
                    for k in range(1, NFLAT + 1):
                        try:
                            cur.append(bezierTools.splitQuadraticAtT(*P, k / NFLAT)[0][-1])
                        except Exception:
                            pass
                    last = pts[i + 1]
            else:
                cur.append(pts[0])
                last = pts[0]
        elif op == 'closePath':
            if len(cur) > 1:
                out.append(np.array(cur))
            cur = []
            last = None
    if len(cur) > 1:
        out.append(np.array(cur))
    return [c for c in out if len(c) >= 3]


def draw_pts(gs, gn):
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        return None
    if not rp.value:
        return None
    return contour_pts_from_rp(rp.value)


def min_gap(cs):
    """返回 (最小缝隙, 轮廓对)。只比较 bbox 邻近的轮廓对以提高速度。"""
    n = len(cs)
    if n < 2:
        return None
    boxes = [(c[:, 0].min(), c[:, 0].max(), c[:, 1].min(), c[:, 1].max()) for c in cs]
    best = None
    for i in range(n):
        for j in range(i + 1, n):
            bx1 = boxes[i]; bx2 = boxes[j]
            # bbox 距离（若已超过 GAP_MAX 就跳过）
            dx = max(0.0, max(bx1[0], bx2[0]) - min(bx1[1], bx2[1]))
            dy = max(0.0, max(bx1[2], bx2[2]) - min(bx1[3], bx2[3]))
            if dx > GAP_MAX or dy > GAP_MAX:
                continue
            # 只取邻近区域内的点
            a = cs[i]; b = cs[j]
            if len(a) > 400:
                a = a[::max(1, len(a) // 400)]
            if len(b) > 400:
                b = b[::max(1, len(b) // 400)]
            d2 = ((a[:, None, :] - b[None, :, :]) ** 2).sum(axis=2)
            d = float(np.sqrt(d2.min()))
            if best is None or d < best[0]:
                best = (d, i, j)
    return best


def scan(path, cps):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    res = {}
    for cp in cps:
        gn = cm.get(cp)
        if gn is None:
            continue
        cs = draw_pts(gs, gn)
        if not cs:
            continue
        mg = min_gap(cs)
        if mg is None:
            continue
        res[cp] = mg
    f.close()
    return res


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = [ord(c) for c in common]
    fo = TTFont(OURS, lazy=True); cmo = fo.getBestCmap(); fo.close()
    cps = [cp for cp in cps if cp in cmo]
    print('扫描 %d 字' % len(cps), flush=True)

    print('  我们...', flush=True)
    A = scan(OURS, cps)
    print('    %d 字有结果, %.0fs' % (len(A), time.time() - t0), flush=True)

    print('  SHS...', flush=True)
    B = scan(SHS, cps)
    print('    %d 字有结果, %.0fs' % (len(B), time.time() - t0), flush=True)

    # 找出「我们有缝隙但 SHS 没有」的字
    regress = []
    for cp in cps:
        a = A.get(cp); b = B.get(cp)
        if not a or not b:
            continue
        d_ours = a[0]; d_shs = b[0]
        if GAP_MIN <= d_ours <= GAP_MAX and d_shs < GAP_MIN:
            regress.append((round(d_ours, 2), round(d_shs, 2), chr(cp), a[1], a[2], b[1], b[2]))
    regress.sort(reverse=True)

    print()
    print('=== 本项目引入的缝隙（我们 0.5~10 单位 / SHS 无缝）: %d 字 ===' % len(regress))
    for row in regress[:30]:
        print('  %s 我们%.1f SHS%.2f  轮廓对 %d-%d -> SHS %d-%d' % (row[2], row[0], row[1], row[3], row[4], row[5], row[6]))

    # 统计分布
    dv = np.array([v[0] for v in A.values()])
    db = np.array([v[0] for v in B.values()])
    print()
    print('=== 最小缝隙分布 ===')
    print('  我们: 中位%.2f P90=%.2f 最大%.2f' % (np.median(dv), np.percentile(dv, 90), dv.max()))
    print('  SHS : 中位%.2f P90=%.2f 最大%.2f' % (np.median(db), np.percentile(db, 90), db.max()))
    for lo, hi in [(0.5, 2), (2, 5), (5, 10), (10, 20), (20, 1000)]:
        na = int(((dv >= lo) & (dv < hi)).sum())
        nb = int(((db >= lo) & (db < hi)).sum())
        print('  [%5.1f,%6.1f): 我们 %4d  SHS %4d' % (lo, hi, na, nb))

    json.dump([{'cp': r[2], 'ours': r[0], 'shs': r[1]} for r in regress],
              open(OUT, 'w'), ensure_ascii=False)
    print()
    print('总耗时 %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()