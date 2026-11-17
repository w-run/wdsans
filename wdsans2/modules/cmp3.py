#!/usr/bin/env python3
"""cmp3 - 三处缺陷与参考字体逐像素对比"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [
  ('我们', '/workspace/static/wdsans/WDesignSans-VF.otf'),
  ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('HOS',  '/workspace/wdsans/ref/hos/hos-400.ttf'),
  ('OPPO', '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
]
SZ = 600


def stats(path, ch, region):
    """region=(x0,x1,y0,y1) 为字面相对比例"""
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    a = np.array(img) > 100
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    y0, y1, x0, x1 = rows[0], rows[-1], cols[0], cols[-1]
    h = y1 - y0; w = x1 - x0
    ry0 = int(y0 + h*region[2]); ry1 = int(y0 + h*region[3])
    rx0 = int(x0 + w*region[0]); rx1 = int(x0 + w*region[1])
    sub = a[ry0:ry1, rx0:rx1]
    return int(sub.sum()), w, h


# 到：顶部横笔区域（顶端 8%）
print('=== 到：顶端 10% 区域的墨量 / 分布 ===')
for lbl, p in FONTS:
    ink, w, h = stats(p, "到", (0, 1, 0, 0.10))
    print("  %-5s 墨量%6d  字面%dx%d" % (lbl, ink, w, h))

print()
# 出：右下脚区域（底部 15%，右侧 30%）
print('=== 出：底部 15% × 右侧 30% 区域 ===')
for lbl, p in FONTS:
    ink, w, h = stats(p, "出", (0.7, 1.0, 0.85, 1.0))
    print("  %-5s 墨量%6d  字面%dx%d" % (lbl, ink, w, h))

print()
# 永：竖弯钩底部（底部 8%，中部）
print('=== 永：底部 8% × 中部 40% 区域 ===')
for lbl, p in FONTS:
    ink, w, h = stats(p, "永", (0.25, 0.7, 0.92, 1.0))
    print("  %-5s 墨量%6d  字面%dx%d" % (lbl, ink, w, h))