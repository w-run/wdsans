#!/usr/bin/env python3
"""ledge_ink - 位图度量「顶部横笔相对长度」，找仍偏短的字

思路:
  1. 渲染单字，取顶部 12% 高度带
  2. 计算该带内墨迹的 x 跨度 / 字面宽
  3. 与 OPPO/HOS 对比，找我们明显偏短的字

优点: 完全不受轮廓拆分方式影响，是最接近视觉的度量。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [("我们", "/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("HOS",  "/workspace/wdsans/ref/hos/hos-400.ttf"),
         ("OPPO", "/workspace/wdsans/ref/ops4/OPPOSans4.ttf")]
SIZE = 300
BAND = 0.12      # 顶部 12% 高度带


def topratio(path, ch):
    try:
        ft = ImageFont.truetype(path, SIZE)
    except Exception:
        return None
    img = Image.new("L", (SIZE * 2, SIZE * 2), 0)
    ImageDraw.Draw(img).text((SIZE // 3, SIZE // 3), ch, fill=255, font=ft)
    a = np.array(img) > 100
    if not a.any():
        return None
    rows = np.where(a.any(axis=1))[0]
    cols = np.where(a.any(axis=0))[0]
    h = rows[-1] - rows[0] + 1
    w = cols[-1] - cols[0] + 1
    band = a[rows[0]:rows[0] + max(2, int(h * BAND))]
    bc = np.where(band.any(axis=0))[0]
    if len(bc) < 2:
        return None
    return (bc[-1] - bc[0] + 1) / w


CH = '各冬条备务夏麦玫玖退腿很根跟眼银艰限浪郎朗良食养美亲新斯斯'
print('=== 顶部 12%% 高度带的墨迹跨度 / 字面宽 ===')
print('%-4s %-9s %-9s %-9s %-8s' % ('字', '我们', 'HOS', 'OPPO', '判定'))
bad = []
for ch in CH:
    vals = [topratio(p, ch) for _, p in FONTS]
    if any(v is None for v in vals):
        continue
    ref = max(vals[1], vals[2])
    diff = (vals[0] - ref) / ref * 100 if ref > 0 else 0
    flag = '偏短' if diff < -12 else ('ok' if diff > -8 else '接近')
    if diff < -12:
        bad.append((ch, vals[0], ref, diff))
    print('%-4s %-9.3f %-9.3f %-9.3f %-8s (%+.0f%%)' % (ch, vals[0], vals[1], vals[2], flag, diff))
print()
print('明显偏短(%d): %s' % (len(bad), ' '.join(b[0] for b in bad)))