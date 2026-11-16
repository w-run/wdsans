#!/usr/bin/env python3
"""m_curvflat - 长曲线曲率压平（OPPO/HOS 风格）

量化发现（2026-11-15，用 fontTools bezierTools + 官方采样）:

  长曲线（chord >= 300）的最大偏离弦距离:
    字体    中位   均值    P75     P90
    我们    66.8   68.0   108.8   136.9   em
    OPPO    19.2   18.7    23.5    25.7
    HOS     17.1   23.4    31.6    50.2

  -> 我们的长曲线弯曲度是 OPPO/HOS 的 3.5 倍

  曲率<0.995 的"真弯"长曲线占比:
    我们 127/167 = 76.0%
    OPPO   67/378 = 17.7%
    HOS    55/302 = 18.2%

修法（只改控制点，不改段数与操作符 -> 三档天然一致）:
  对每条命中曲线，把两个控制点 P1/P2 向「弦」靠拢：
      P1' = A + (P1 - A) * k      其中 k 由目标偏离量反解
      P2' = B + (P2 - B) * k
  这保持端点不动（字形骨架不变），只减小鼓出量。

  k 的反解: 三次贝塞尔最大偏离 ≈ (3*sqrt(3)/4) * |...|，
  但直接数值求解更可靠: 二分搜索 k 使偏离 <= target_dev。

🔴 400 档驱动，三档同一索引
"""
import sys, os, json
import numpy as np
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.misc import bezierTools
from canonpen3 import contours_from_pen, make_charstring

SRC = os.environ.get('WDS_SRC', '/workspace/wdsans2/build/masters_MOD24')
OUTD = os.environ.get('WDS_OUT', '/workspace/wdsans2/build/masters_MOD26')
FN = {'250': 'master-ExtraLight-250.otf', '400': 'master-Regular-400.otf',
      '900': 'master-Heavy-900.otf'}
SW = {'250': 30.0, '400': 77.0, '900': 150.0}

MIN_CHORD = 300.0        # 只处理长曲线
TARGET_DEV = {"250": 4.0, "400": 10.0, "900": 20.0}   # 温和版(减半)


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def samp(P, n=10):
    P = [np.array(p, float) for p in P]
    if len(P) == 4:
        return [bezierTools.splitCubicAtT(P[0], P[1], P[2], P[3], i / n)[0][-1]
                for i in range(n + 1)]
    if len(P) == 3:
        return [bezierTools.splitQuadraticAtT(P[0], P[1], P[2], i / n)[0][-1]
                for i in range(n + 1)]
    return []


def maxdev(P, n=10):
    S = np.array(samp(P, n))
    if len(S) < 3:
        return 0.0
    A = S[0]; B = S[-1]
    ab = B - A
    L = float(np.linalg.norm(ab))
    if L < 1e-6:
        return 0.0
    nv = np.array([-ab[1], ab[0]]) / L
    return float(np.max(np.abs((S - A) @ nv)))


def squash_cubic(A, P1, P2, B, target):
    """解析法：控制点沿「端点→控制点」方向缩 k 时偏离近似线性，
    故 k ≈ target / dev。取 k 后校验一次，超出则再按比例微调。

    比二分搜索快 ~24 倍（避免 2 万字 x 24 次 x 16 采样 = 数百万次贝塞尔分割）
    """
    dev = maxdev([A, P1, P2, B])
    if dev <= 1e-6:
        return P1, P2, 1.0
    k = target / dev
    if k >= 1.0:
        return P1, P2, 1.0
    Q1 = A + (P1 - A) * k
    Q2 = B + (P2 - B) * k
    # 一次校验 + 线性补偿（偏离的二次项很小）
    d2 = maxdev([A, Q1, Q2, B])
    if d2 > target * 1.02 and d2 > 1e-6:
        k2 = k * (target / d2)
        Q1 = A + (P1 - A) * k2
        Q2 = B + (P2 - B) * k2
        return Q1, Q2, k2
    return Q1, Q2, k


def squash_quad(A, P1, B, target):
    dev = maxdev([A, P1, B])
    if dev <= 1e-6:
        return P1, 1.0
    k = target / dev
    if k >= 1.0:
        return P1, 1.0
    Q1 = A + (P1 - A) * k
    d2 = maxdev([A, Q1, B])
    if d2 > target * 1.02 and d2 > 1e-6:
        k2 = k * (target / d2)
        Q1 = A + (P1 - A) * k2
        return Q1, k2
    return Q1, k


def detect(path400, cm400, gs400):
    """400 档检测，返回 [{g, segs:[(ci,k,typ,k_ratio)]}]"""
    index = []
    tgt = TARGET_DEV['400']
    cjk = [(cp, gn) for cp, gn in cm400.items() if 0x4E00 <= cp <= 0x9FFF]
    for cp, gn in cjk:
        rp = RecordingPen()
        try:
            gs400[gn].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        hits = []
        for ci, c in enumerate(C):
            prev = np.array(c['start'], float)
            for k, s in enumerate(c['segs']):
                if s[0] == 'C':
                    pts = [prev, np.array(s[1], float), np.array(s[2], float),
                           np.array(s[3], float)]
                    d = float(np.linalg.norm(pts[-1] - pts[0]))
                    if d >= MIN_CHORD:
                        md = maxdev(pts)
                        if md > tgt:
                            _, _, kk = squash_cubic(pts[0], pts[1], pts[2], pts[3], tgt)
                            hits.append([ci, k, 'C', round(float(kk), 6)])
                    prev = np.array(s[3], float)
                elif s[0] == 'Q':
                    pts = [prev, np.array(s[1], float), np.array(s[2], float)]
                    d = float(np.linalg.norm(pts[-1] - pts[0]))
                    if d >= MIN_CHORD:
                        md = maxdev(pts)
                        if md > tgt:
                            _, kk = squash_quad(pts[0], pts[1], pts[2], tgt)
                            hits.append([ci, k, 'Q', round(float(kk), 6)])
                    prev = np.array(s[2], float)
                else:
                    prev = endp(s)
        if hits:
            index.append({'g': gn, 'cp': cp, 'hits': hits})
    return index


def main():
    os.makedirs(OUTD, exist_ok=True)

    f400 = TTFont(SRC + '/' + FN['400'])
    cm400 = f400.getBestCmap()
    gs400 = f400.getGlyphSet()
    index = detect(SRC + '/' + FN['400'], cm400, gs400)
    f400.close()
    ncurve = sum(len(it['hits']) for it in index)
    print('命中 %d 字 / %d 条曲线' % (len(index), ncurve), flush=True)
    with open('/workspace/wdsans2/build/idx_curvflat.json', 'w') as fh:
        json.dump(index, fh)
    if not index:
        return

    for tag in ['250', '400', '900']:
        f = TTFont(SRC + '/' + FN[tag])
        gs = f.getGlyphSet()
        cff2 = f['CFF2'].cff
        td = cff2[cff2.fontNames[0]]
        csT = td.CharStrings
        tgt = TARGET_DEV[tag]

        done = 0
        skip = 0
        for it in index:
            gn = it['g']
            rp = RecordingPen()
            try:
                gs[gn].draw(rp)
            except Exception:
                skip += 1
                continue
            C = contours_from_pen(rp.value)
            NEW = []
            hit_map = {}
            for ci, k, typ, _ in it['hits']:
                hit_map[(ci, k)] = typ
            ok = True
            for ci, c in enumerate(C):
                prev = np.array(c['start'], float)
                segs_out = []
                for k, s in enumerate(c['segs']):
                    if (ci, k) in hit_map:
                        if s[0] == 'C':
                            A = prev; P1 = np.array(s[1], float)
                            P2 = np.array(s[2], float); B = np.array(s[3], float)
                            d = float(np.linalg.norm(B - A))
                            if d >= 1e-6:
                                Q1, Q2, _ = squash_cubic(A, P1, P2, B, tgt)
                                segs_out.append(['C', (Q1[0], Q1[1]),
                                                 (Q2[0], Q2[1]), (B[0], B[1])])
                            else:
                                segs_out.append(list(s))
                            prev = B
                        elif s[0] == 'Q':
                            A = prev; P1 = np.array(s[1], float); B = np.array(s[2], float)
                            d = float(np.linalg.norm(B - A))
                            if d >= 1e-6:
                                Q1, _ = squash_quad(A, P1, B, tgt)
                                segs_out.append(['Q', (Q1[0], Q1[1]), (B[0], B[1])])
                            else:
                                segs_out.append(list(s))
                            prev = B
                        else:
                            segs_out.append(list(s))
                            prev = endp(s)
                    else:
                        segs_out.append(list(s))
                        prev = endp(s)
                NEW.append({'start': (c['start'][0], c['start'][1]), 'segs': segs_out})
            old = csT[gn]
            csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
            done += 1

        print('  %s: 应用 %d, 跳过 %d (目标偏离 %.0f em)'
              % (tag, done, skip, tgt), flush=True)
        f['post'].formatType = 3.0
        f['post'].glyphOrder = None
        f.save(OUTD + '/' + FN[tag])
        f.close()


main()
