#!/usr/bin/env python3
"""trace3_bmp - 用位图逐行扫描，对比三处缺陷的几何差异"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',  BASE + 'masters_T6/master-Regular-400.otf'),
  ('MOD', BASE + 'masters_MOD/master-Regular-400.otf'),
  ('R4',  BASE + 'masters_R4/master-Regular-400.otf'),
  ('R10', BASE + 'masters_R10/master-Regular-400.otf'),
  ('R15', BASE + 'masters_R15/master-Regular-400.otf'),
  ('R16', BASE + 'masters_R16/master-Regular-400.otf'),
  ('R25b',BASE + 'masters_R25b/master-Regular-400.otf'),
  ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf'),
]

SZ = 800


def render(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    a = np.array(img) > 100
    rows = np.where(a.any(axis=1))[0]
    cols = np.where(a.any(axis=0))[0]
    return a, rows[0], rows[-1], cols[0], cols[-1]


def scanline(a, y0, y1, frac):
    y = int(y0 + (y1 - y0) * frac)
    xs = np.where(a[y])[0]
    if not len(xs): return []
    runs = []; st = xs[0]; pv = xs[0]
    for x in xs[1:]:
        if x - pv > 2:
            runs.append((st, pv)); st = x
        pv = x
    runs.append((st, pv))
    return runs


TESTS = [
  ('到 顶部横笔', '到', 0.92, '右端 reach'),
  ('出 右下脚', '出', 0.92, '底部墨段'),
  ('永 竖弯钩', '永', 0.95, '底部墨段'),
]

for title, ch, frac, note in TESTS:
    print("=" * 62)
    print("【%s】%s  (从顶往下 %d%%)" % (title, note, frac*100))
    print("=" * 62)
    for lbl, p in STAGES:
        if not os.path.exists(p):
            continue
        try:
            a, r0, r1, c0, c1 = render(p, ch)
        except Exception:
            continue
        runs = scanline(a, r0, r1, frac)
        w = c1 - c0
        rel = [(round((s-c0)/w*100), round((e-c0)/w*100)) for s, e in runs]
        print("  %-5s 字面宽%d  相对位置%%: %s" % (lbl, w, rel))
    print()