#!/usr/bin/env python3
"""frag_detail - 定位 嘴/眠 的碎裂位置"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

FONTS = [("我们", "/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("SHS",  "/workspace/wdsans/ref/shs/shs-400.otf"),
         ("HOS",  "/workspace/wdsans/ref/hos/hos-400.ttf")]
SIZE = 400


def analyze(ch):
    print("=== %s ===" % ch)
    for lbl, p in FONTS:
        ft = ImageFont.truetype(p, SIZE)
        img = Image.new("L", (SIZE * 2, SIZE * 2), 0)
        ImageDraw.Draw(img).text((SIZE // 3, SIZE // 3), ch, fill=255, font=ft)
        a = np.array(img) > 100
        if not a.any():
            print("  %s 空" % lbl)
            continue
        lab, n = ndimage.label(a)
        sizes = ndimage.sum(a, lab, range(1, n + 1))
        rows = np.where(a.any(axis=1))[0]
        cols = np.where(a.any(axis=0))[0]
        print("  %-5s %d 块  bbox x[%d,%d] y[%d,%d]" % (lbl, n, cols[0], cols[-1], rows[0], rows[-1]))
        # 每块的位置与大小
        order = np.argsort(sizes)[::-1]
        for k in order[:8]:
            m = lab == (k + 1)
            r = np.where(m.any(axis=1))[0]
            c = np.where(m.any(axis=0))[0]
            print("      块%d 面积%5d  x[%3d,%3d] y[%3d,%3d]" % (k + 1, int(sizes[k]), c[0], c[-1], r[0], r[-1]))


for ch in ["嘴", "眠"]:
    analyze(ch)
    print()