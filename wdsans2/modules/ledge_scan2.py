#!/usr/bin/env python3
"""ledge_scan2 - 全库找「顶部横笔右余 > 目标」但未处理的字

不预设轮廓形态（3段/4段L、含曲线都行），只看几何事实:
  1. 找到字形内 y 最高的横笔状轮廓（宽/高 >= 3）
  2. 计算它的右端到字形右界的距离（右余）
  3. 右余 > TARGET_MARGIN 的字 = 真正的待办

对照 OPPO/HOS 判断是否真的该延伸。
"""
import sys, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'

TARGET = 90      # 400 档目标右余


def contours(path):
    """一次打开，返回 {cp: [轮廓点集,...]}"""
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in cm:
        if not (0x4E00 <= cp <= 0x9FFF):
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


def topbar_rightmargin(cs):
    """返回 (右余, 横笔宽, 横笔x范围, 字形右界)；找不到横笔返回 None"""
    if not cs:
        return None
    allx = np.vstack(cs)[:, 0]
    gx1 = allx.max()
    gmax = max(c[:, 1].max() for c in cs)
    best = None
    for c in cs:
        x0, x1 = c[:, 0].min(), c[:, 0].max()
        y0, y1 = c[:, 1].min(), c[:, 1].max()
        w = x1 - x0
        h = y1 - y0
        if h < 1:
            h = 1
        # 横笔: 又宽又扁，且靠近字形顶部
        if w / h < 3.0:
            continue
        if y1 < gmax - 180:
            continue
        margin = gx1 - x1
        if best is None or margin < best[0]:
            best = (margin, w, x0, x1, gx1)
    return best


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cps = [ord(c) for c in dict.fromkeys(common)]
    print("%d 字" % len(cps), flush=True)

    print("读我们...", flush=True)
    A = contours(OURS)
    print("   %.0fs" % (time.time() - t0), flush=True)
    print("读 HOS...", flush=True)
    B = contours(HOS)
    print("   %.0fs" % (time.time() - t0), flush=True)

    rows = []
    for cp in cps:
        a = A.get(cp)
        if not a:
            continue
        ra = topbar_rightmargin(a)
        if not ra:
            continue
        m_ours = ra[0]
        if m_ours <= TARGET:
            continue
        b = B.get(cp)
        m_hos = topbar_rightmargin(b)[0] if b and topbar_rightmargin(b) else None
        rows.append((round(m_ours, 0), round(m_hos, 0) if m_hos is not None else -1, chr(cp)))

    rows.sort(reverse=True)
    print()
    print("=== 顶部横笔右余 > %d 的字: %d ===" % (TARGET, len(rows)))
    print("%-4s %-8s %-8s" % ("字", "我们", "HOS"))
    for m, h, ch in rows[:40]:
        print("%-4s %-8.0f %-8s" % (ch, m, ("%.0f" % h) if h >= 0 else "-"))

    dv = np.array([r[0] for r in rows])
    print()
    if len(dv):
        print("右余分布: 中位%.0f P90=%.0f 最大%.0f" %
              (np.median(dv), np.percentile(dv, 90), dv.max()))
    print("总耗时 %.0fs" % (time.time() - t0))


if __name__ == '__main__':
    main()