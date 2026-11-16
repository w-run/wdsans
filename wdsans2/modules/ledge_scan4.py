#!/usr/bin/env python3
"""ledge_scan4 - 加横笔宽度判据，排除左侧偏旁"""
import sys, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'

TARGET = 95
MIN_W = 380


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


def topbar_info(cs, min_w=MIN_W):
    if not cs:
        return None
    allP = np.vstack(cs)
    gmax = allP[:, 1].max()
    cands = []
    for i, c in enumerate(cs):
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        w = x1 - x0
        h = max(y1 - y0, 1)
        if w < min_w:
            continue
        if w / h < 2.5:
            continue
        if y1 < gmax - 260:
            continue
        cands.append((y1, i, x0, x1, y0, y1))
    if not cands:
        return None
    cands.sort(reverse=True)
    y1, i, x0, x1, y0, y1b = cands[0]
    right = x1
    for j, c in enumerate(cs):
        if j == i:
            continue
        cy0, cy1 = c[:, 1].min(), c[:, 1].max()
        if cy1 < y0 or cy0 > y1b:
            continue
        right = max(right, c[:, 0].max())
    return (right - x1, x1 - x0, x0, x1, y0, y1b)


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = set(ord(c) for c in dict.fromkeys(common))
    A = contours(OURS, cps)
    needed = set()
    for cp in A:
        r = topbar_info(A[cp])
        if r and r[0] > TARGET:
            needed.add(cp)
    print("%d 字 -> 待核查 %d" % (len(cps), len(needed)), flush=True)
    B = contours(HOS, needed)
    C = contours(OPPO, needed)

    rows = []
    for cp in needed:
        ra = topbar_info(A.get(cp))
        if not ra:
            continue
        rb = topbar_info(B.get(cp)) if cp in B else None
        rc = topbar_info(C.get(cp)) if cp in C else None
        refs = [r[0] for r in (rb, rc) if r]
        if not refs:
            continue
        ref = min(refs)
        if ref > TARGET:
            continue
        rows.append((ra[0], ref, ra[1], chr(cp), ra[2], ra[3]))

    rows.sort(reverse=True)
    print()
    print("=== 顶部主横笔右余 > %d 且参考 <= %d: %d 字 ===" % (TARGET, TARGET, len(rows)))
    print("%-4s %-7s %-7s %-7s %s" % ("字", "我们", "参考", "横笔宽", "x范围"))
    for m, r, w, ch, x0, x1 in rows[:50]:
        print("%-4s %-7.0f %-7.0f %-7.0f x[%.0f,%.0f]" % (ch, m, r, w, x0, x1))
    print()
    print("总耗时 %.0fs" % (time.time() - t0))


if __name__ == '__main__':
    main()