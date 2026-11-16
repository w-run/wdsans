#!/usr/bin/env python3
"""ledge_scan5 - 加「横笔居中」判据，精确定位横折出头"""
import sys, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'

TARGET = 95
MIN_W = 350
CENTER_TOL = 120


def contours(path, cps=None):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in cm:
        if not (0x4E00 <= cp <= 0x9FFF):
            continue
        if cps is not None and cp not in cps:
            continue
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        cs = []
        cur = None
        for op, args in rp.value:
            if op == "moveTo":
                if cur and len(cur) >= 3:
                    cs.append(np.array(cur))
                cur = [np.array(args[0], float)]
            elif op == "lineTo":
                cur.append(np.array(args[0], float))
            elif op in ("curveTo", "qCurveTo"):
                cur.extend([np.array(a, float) for a in args])
            elif op == "closePath":
                if cur and len(cur) >= 3:
                    cs.append(np.array(cur))
                cur = None
        if cur and len(cur) >= 3:
            cs.append(np.array(cur))
        if cs:
            out[cp] = cs
    f.close()
    return out


def topbar(cs):
    """返回 (右余, 横笔宽, 中心x, x0, x1, y0, y1, 字形中心) 或 None"""
    if not cs:
        return None
    allP = np.vstack(cs)
    gmax = allP[:, 1].max()
    gx0, gx1 = allP[:, 0].min(), allP[:, 0].max()
    gcen = (gx0 + gx1) / 2
    cands = []
    for i, c in enumerate(cs):
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        w = x1 - x0
        h = max(y1 - y0, 1)
        if w < MIN_W:
            continue
        if w / h < 2.0:
            continue
        if y1 < gmax - 280:
            continue
        cen = (x0 + x1) / 2
        if abs(cen - gcen) > CENTER_TOL:
            continue      # 不是居中的顶部横笔（是左侧偏旁）
        cands.append((y1, i, x0, x1, y0, y1, cen))
    if not cands:
        return None
    cands.sort(reverse=True)
    y1, i, x0, x1, y0, y1b, cen = cands[0]
    right = x1
    for j, c in enumerate(cs):
        if j == i:
            continue
        cy0, cy1 = c[:, 1].min(), c[:, 1].max()
        if cy1 < y0 or cy0 > y1b:
            continue
        right = max(right, c[:, 0].max())
    return (right - x1, x1 - x0, cen, x0, x1, y0, y1b, gcen)


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = set(ord(c) for c in dict.fromkeys(common))
    A = contours(OURS, cps)
    needed = set()
    for cp in A:
        r = topbar(A[cp])
        if r and r[0] > TARGET:
            needed.add(cp)
    print("%d 字 -> 待核查 %d" % (len(cps), len(needed)), flush=True)
    B = contours(HOS, needed)
    C = contours(OPPO, needed)
    rows = []
    for cp in needed:
        ra = topbar(A.get(cp))
        rb = topbar(B.get(cp)) if cp in B else None
        rc = topbar(C.get(cp)) if cp in C else None
        refs = [r[0] for r in (rb, rc) if r]
        if not refs:
            continue
        ref = min(refs)
        if ref > TARGET:
            continue
        rows.append((ra[0], ref, ra[1], chr(cp), ra[3], ra[4], ra[2], ra[7]))
    rows.sort(reverse=True)
    print()
    print("=== 居中顶部横笔、右余 > %d、参考 <= %d: %d 字 ===" % (TARGET, TARGET, len(rows)))
    print("%-4s %-7s %-7s %-7s %-14s %s" % ("字","我们","参考","横笔宽","横笔x","中心/字心"))
    for m, r, w, ch, x0, x1, cen, gcen in rows:
        print("%-4s %-7.0f %-7.0f %-7.0f [%.0f,%.0f]  %.0f/%.0f" % (ch, m, r, w, x0, x1, cen, gcen))
    print()
    print("字数: %d  |  %.0fs" % (len(rows), time.time() - t0))


if __name__ == '__main__':
    main()