#!/usr/bin/env python3
"""final_check - 验证三处缺陷"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
SZ = 600


def top_ink(path, ch, region):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    a = np.array(img) > 100
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    y0, y1, x0, x1 = rows[0], rows[-1], cols[0], cols[-1]
    h = y1-y0; w = x1-x0
    ry0 = int(y0 + h*region[2]); ry1 = int(y0 + h*region[3])
    rx0 = int(x0 + w*region[0]); rx1 = int(x0 + w*region[1])
    return int(a[ry0:ry1, rx0:rx1].sum())


print('=== 到 顶端 10% 墨量（应接近 SHS）===')
for lbl, p in [('修前R16','/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'),
               ('修后VF', VF),
               ('SHS', SHS)]:
    print("  %-9s %d" % (lbl, top_ink(p, "到", (0,1,0,0.10))))

print()
print('=== 各 顶端 10% 墨量（应保留延伸）===')
for lbl, p in [('R15原始','/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'),
               ('修后VF', VF),
               ('SHS', SHS)]:
    print("  %-9s %d" % (lbl, top_ink(p, "各", (0,1,0,0.10))))