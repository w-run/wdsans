#!/usr/bin/env python3
"""frag_ink - 位图墨量对比（最可靠）"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [("我们", "/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("SHS",  "/workspace/wdsans/ref/shs/shs-400.otf"),
         ("HOS",  "/workspace/wdsans/ref/hos/hos-400.ttf"),
         ("OPPO", "/workspace/wdsans/ref/ops4/OPPOSans4.ttf")]
SIZE = 400


def ink(path, ch):
    ft = ImageFont.truetype(path, SIZE)
    img = Image.new("L", (SIZE * 2, SIZE * 2), 0)
    ImageDraw.Draw(img).text((SIZE // 3, SIZE // 3), ch, fill=255, font=ft)
    a = np.array(img)
    m = a > 100
    if not m.any():
        return None
    # 归一化: 墨量 / bbox面积
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    bbox = (rows[-1] - rows[0] + 1) * (cols[-1] - cols[0] + 1)
    return int(m.sum()), bbox, int(m.sum()) / bbox * 100


print("=== 墨量对比（墨像素 / bbox% ）===")
print("%-4s %-18s %-18s %-18s %-18s" % ("字", "我们", "SHS", "HOS", "OPPO"))
for ch in "嘴眠靡廖签窘熔赊秩窝滁愉臆敝捧爵":
    row = [ch]
    for lbl, p in FONTS:
        r = ink(p, ch)
        row.append("%6d/%4.1f%%" % (r[0], r[2]) if r else "-")
    print("%-4s %-18s %-18s %-18s %-18s" % tuple(row))