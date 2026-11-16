#!/usr/bin/env python3
"""scan_frag - 全库位图碎裂度统计

思路: 在小字号（实际使用尺寸）渲染，统计墨迹连通块数。
缝隙会在小字号下把笔画切断 -> 连通块变多。
对比我们 vs SHS 的「块数差值」分布，找系统性碎裂。

用 scipy.ndimage.label 加速（比手写 flood fill 快 100 倍）。
"""
import sys, json, time
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
try:
    from scipy import ndimage
except ImportError:
    ndimage = None

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
SIZE = 96


def regions(path, chs, size=SIZE):
    ft = ImageFont.truetype(path, size)
    out = []
    for ch in chs:
        img = Image.new("L", (size * 2, size * 2), 0)
        ImageDraw.Draw(img).text((size // 4, size // 4), ch, fill=255, font=ft)
        a = np.array(img) > 100
        if not a.any():
            out.append(None)
            continue
        lab, n = ndimage.label(a)
        out.append(n)
    return out


def main():
    t0 = time.time()
    common = open('/workspace/wdsans2/data/common3500.txt', encoding='utf-8').read().strip()
    chs = list(dict.fromkeys(common))
    print('%d 字, 字号 %dpx' % (len(chs), SIZE), flush=True)

    print('  我们...', flush=True)
    A = regions(OURS, chs)
    print('    %.0fs' % (time.time() - t0), flush=True)
    print('  SHS...', flush=True)
    B = regions(SHS, chs)
    print('    %.0fs' % (time.time() - t0), flush=True)

    diffs = []
    for ch, a, b in zip(chs, A, B):
        if a is None or b is None:
            continue
        diffs.append((a - b, ch, a, b))

    d = np.array([x[0] for x in diffs])
    print()
    print('=== 连通块数差值（我们 - SHS）===')
    print('  中位 %.1f  均值 %.2f  n=%d' % (np.median(d), d.mean(), len(d)))
    for lo, hi, lbl in [(-100, -2, '我们更完整'), (-2, 0, '略好'),
                        (0, 1, '相同'), (1, 3, '略碎'), (3, 1000, '明显更碎')]:
        n = int(((d >= lo) & (d < hi)).sum())
        print('  %-8s [%4d,%5d): %4d  (%4.1f%%)' % (lbl, lo, hi, n, n / len(d) * 100))

    worse = sorted([x for x in diffs if x[0] >= 3], reverse=True)
    print()
    print('=== 明显更碎的字: %d ===' % len(worse))
    for dd, ch, a, b in worse[:25]:
        print('  %s 我们%d块 SHS%d块 (+%d)' % (ch, a, b, dd))

    json.dump([{'ch': x[1], 'ours': x[2], 'shs': x[3]} for x in worse],
              open('/workspace/wdsans2/build/scan_frag.json', 'w'), ensure_ascii=False)
    print()
    print('总耗时 %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()