#!/usr/bin/env python3
# corner_scan - 逐行扫描拐角区墨段, 找凹口
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 1600; UPEM = 1000

def scan(path, lbl, ch="多", x0=680, x1=800, y0=660, y1=770):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    H, W = sub.shape
    k = UPEM / SZ
    # 把 em 坐标换算成像素：字形左缘 = cols[0] -> em 0? 不精确,
    # 改为直接输出每行的墨段 (em 相对字形宽度归一化)
    print("=== %s  bmp %dx%d ===" % (lbl, W, H))
    print("   y_em   墨段(像素x)             段数  右缘_em(归一化)")
    n = 24
    for i in range(n+1):
        yy = int(H * (0.13 + 0.30 * i / n))
        row = sub[yy]
        xs = np.where(row)[0]
        if not len(xs):
            print("   %-6.0f (空)" % (yy*k)); continue
        runs = []
        st = xs[0]; pv = xs[0]
        for x in xs[1:]:
            if x - pv > 1:
                runs.append((st, pv)); st = x
            pv = x
        runs.append((st, pv))
        rs = " ".join("[%d-%d]" % r for r in runs)
        print("   %-6.0f %-26s %-5d %.3f" % (yy*k, rs, len(runs), xs[-1]/W))
    print()

scan("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf", "R32-250")
scan("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO-400")