#!/usr/bin/env python3
"""ledge_scan3 - 正确的判据: 找「y 最高的横笔轮廓」比较其右余

v2 的问题: 488 字多为左右结构，右余大是因为右边还有部件。
正确做法: 只在该横笔「自身的 y 带」内找字形右界，不看整字右界。
"""
import sys, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'

TARGET = 95


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


def topbar_gap(cs):
    """返回 (右余, 横笔宽, 横笔y带)。
    右余 = 该横笔 y 带内、其它轮廓的最右 x - 横笔右端。"""
    if not cs:
        return None
    allP = np.vstack(cs)
    gmax = allP[:, 1].max()
    # 找最靠顶的宽扁轮廓
    cands = []
    for i, c in enumerate(cs):
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        w = x1 - x0
        h = max(y1 - y0, 1)
        if w / h < 2.5:
            continue
        if y1 < gmax - 220:
            continue
        cands.append((y1, i, x0, x1, y0, y1))
    if not cands:
        return None
    cands.sort(reverse=True)
    y1, i, x0, x1, y0, y1b = cands[0]
    # 在该横笔的 y 带内，找所有轮廓的最右 x
    band_lo = y0
    band_hi = y1b
    right = x1
    for j, c in enumerate(cs):
        if j == i:
            continue
        cy0, cy1 = c[:, 1].min(), c[:, 1].max()
        # y 区间有重叠
        if cy1 < band_lo or cy0 > band_hi:
            continue
        right = max(right, c[:, 0].max())
    return (right - x1, x1 - x0, y0, y1b)


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = set(ord(c) for c in dict.fromkeys(common))
    print("%d 字" % len(cps), flush=True)

    A = contours(OURS, cps)
    print("  我们 %.0fs" % (time.time() - t0), flush=True)
    needed = set(cp for cp in A if (lambda r: r and r[0] > TARGET)(topbar_gap(A[cp])))
    print("  待核查 %d 字" % len(needed), flush=True)
    B = contours(HOS, needed)
    C = contours(OPPO, needed)
    print("  HOS/OPPO %.0fs" % (time.time() - t0), flush=True)

    rows = []
    for cp in needed:
        ra = topbar_gap(A.get(cp))
        if not ra:
            continue
        rb = topbar_gap(B.get(cp)) if cp in B else None
        rc = topbar_gap(C.get(cp)) if cp in C else None
        refs = [r[0] for r in (rb, rc) if r]
        if not refs:
            continue
        # 参考字体右余都很小（<=TARGET）才说明我们该改
        ref = min(refs)
        if ref > TARGET:
            continue
        rows.append((ra[0], ref, ra[1], chr(cp)))

    rows.sort(reverse=True)
    print()
    print("=== 我们右余 > %d 且参考右余 <= %d: %d 字 ===" % (TARGET, TARGET, len(rows)))
    print("%-4s %-8s %-8s %-8s" % ("字", "我们", "参考", "横笔宽"))
    for m, r, w, ch in rows[:40]:
        print("%-4s %-8.0f %-8.0f %-8.0f" % (ch, m, r, w))
    print()
    print("总耗时 %.0fs" % (time.time() - t0))


if __name__ == '__main__':
    main()