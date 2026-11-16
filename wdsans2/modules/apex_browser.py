#!/usr/bin/env python3
"""apex_browser - 浏览器截图验证四体平顶"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [('静态版', '/workspace/static/wdsans/WDesignSans-FlatApex-Regular.otf'),
         ('可变版', '/workspace/static/wdsans/WDesignSans-VF.otf'),
         ('OPPO',   '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
         ('HOS',    '/workspace/wdsans/ref/hos/hos-400.ttf')]

SIZE = 400


def topw(path, ch):
    try:
        ft = ImageFont.truetype(path, SIZE)
    except Exception:
        return None
    img = Image.new('L', (SIZE*2, SIZE*2), 0)
    ImageDraw.Draw(img).text((SIZE//2, SIZE//2), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    if len(rows) == 0:
        return None
    top = rows[0]
    # 顶部 3 行内的墨宽
    seg = a[top:top+3]
    cols = np.where(seg.any(axis=0))[0]
    if len(cols) < 2:
        return 0
    return int(cols[-1] - cols[0])


print('=== 浏览器位图顶部墨宽（400px 字号）===')
hdr = ('字',) + tuple(f[0] for f in FONTS)
print('%-4s %-10s %-10s %-10s %-10s' % hdr)
for ch in '今合会含令全金余介企':
    vals = [topw(p, ch) for _, p in FONTS]
    row = [ch] + [('%3d' % v if v is not None else '-') for v in vals]
    print('%-4s %-10s %-10s %-10s %-10s' % tuple(row))
print('')
print('=== 对照组 ===')
for ch in '口回十中申甲田日国目':
    vals = [topw(p, ch) for _, p in FONTS]
    row = [ch] + [('%3d' % v if v is not None else '-') for v in vals]
    print('%-4s %-10s %-10s %-10s %-10s' % tuple(row))