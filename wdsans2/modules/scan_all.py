#!/usr/bin/env python3
"""scan_all - 全库系统扫描：找出与参考字体偏差最大的字

不再凭猜测挑字。对全库 CJK 逐个对比「墨量分布向量」，
找出偏差最大的，再人工判断是否真实缺陷。

墨量分布向量: 4x4 网格各格墨量占比（归一化）
距离度量: L1 距离（各格占比差的绝对值之和，单位百分点）
"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'


def grid_vec(gs, gn, N=4):
    """用 AreaPen 算不出来网格分布，改用轮廓采样点在网格里的面积估算"""
    from fontTools.pens.recordingPen import RecordingPen
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        return None
    if not rp.value:
        return None
    # 用 RecordingPen 的 moveTo/lineTo/curveTo/closePath 近似栅格化
    # 简化: 取所有端点与曲线控制点，按权重计入网格
    xs, ys = [], []
    for op, args in rp.value:
        for pt in args:
            try:
                xs.append(pt[0]); ys.append(pt[1])
            except Exception:
                pass
    if not xs:
        return None
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    w = x1 - x0; h = y1 - y0
    if w < 50 or h < 50:
        return None
    # 栅格化: 用 AreaPen 无法分格，改用在网格中心附近取点的密度
    # 更可靠: 用 bitmap 方式 —— 但全库太慢。折中: 用轮廓点在格中的分布
    grid = np.zeros((N, N))
    for x, y in zip(xs, ys):
        i = min(N - 1, max(0, int((y - y0) / h * N)))
        j = min(N - 1, max(0, int((x - x0) / w * N)))
        grid[i, j] += 1
    tot = grid.sum()
    if tot == 0:
        return None
    return (grid / tot * 100).ravel()


def load_map(path):
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap()
    gs = f.getGlyphSet()
    return f, cm, gs


def main():
    fo, cmo, gso = load_map(OURS)
    fp, cmp_, gsp = load_map(OPPO)
    fh, cmh, gsh = load_map(HOS)

    cjk = [(cp, gn) for cp, gn in cmo.items() if 0x4E00 <= cp <= 0x9FFF]
    print('CJK 共 %d 字' % len(cjk), flush=True)

    # 只扫常用字（前 3500），全库太慢
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    cpset = set(ord(c) for c in common)
    sample = [(cp, gn) for cp, gn in cjk if cp in cpset]
    print('常用字 %d 个' % len(sample), flush=True)

    rows = []
    for idx, (cp, gn) in enumerate(sample):
        vo = grid_vec(gso, gn)
        if vo is None:
            continue
        vp = None; vh = None
        if cp in cmp_:
            vp = grid_vec(gsp, cmp_[cp])
        if cp in cmh:
            vh = grid_vec(gsh, cmh[cp])
        refs = [v for v in (vp, vh) if v is not None]
        if not refs:
            continue
        vr = np.mean(refs, axis=0)
        d = float(np.abs(vo - vr).sum())
        rows.append((d, chr(cp), cp))
        if idx % 500 == 0:
            print('  %d/%d' % (idx, len(sample)), flush=True)

    fo.close(); fp.close(); fh.close()
    rows.sort(reverse=True)
    print()
    print('=== 墨量分布偏差最大的 40 字 ===')
    print('%-4s %-8s %s' % ('字', 'L1距离', '码位'))
    for d, ch, cp in rows[:40]:
        print('%-4s %-8.2f U+%04X' % (ch, d, cp))

    json.dump([{'d': d, 'ch': ch, 'cp': cp} for d, ch, cp in rows[:300]],
              open('/workspace/wdsans2/build/scan_dev.json', 'w'))
    print()
    ds = np.array([r[0] for r in rows])
    print('偏差分布: 中位%.2f 均值%.2f P90=%.2f P99=%.2f 最大%.2f' % (
        np.median(ds), ds.mean(), np.percentile(ds, 90),
        np.percentile(ds, 99), ds.max()))


main()