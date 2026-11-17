#!/usr/bin/env python3
"""digit_weight - 查数字 0-9 笔画粗细是否一致"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
SZ = 600


def stroke_thick(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    a = np.array(img) > 100
    rows = np.where(a.any(axis=1))[0]
    if not len(rows): return None
    y0, y1 = rows[0], rows[-1]
    h = y1 - y0
    # 中部 40%-60% 区间，每行墨段宽度的最小值（笔画厚度）
    ws = []
    for f in np.linspace(0.40, 0.60, 12):
        y = int(y0 + h*f)
        xs = np.where(a[y])[0]
        if not len(xs): continue
        runs = []; st = xs[0]; pv = xs[0]
        for x in xs[1:]:
            if x - pv > 2:
                runs.append(pv - st + 1); st = x
            pv = x
        runs.append(pv - st + 1)
        ws.extend(runs)
    return (min(ws), float(np.median(ws)), max(ws)) if ws else None


print('=== 数字 0-9 笔画厚度 (min/中位/max) ===')
print('%-3s %-22s %-22s' % ('字','我们(VF)','SHS'))
meds = []
for ch in "0123456789":
    a = stroke_thick(VF, ch); b = stroke_thick(SHS, ch)
    if a: meds.append((ch, a[1]))
    print("%-3s %-22s %-22s" % (ch,
        "%d/%.0f/%d" % a if a else "-",
        "%d/%.0f/%d" % b if b else "-"))

if meds:
    v = [m[1] for m in meds]
    print()
    print('中位厚度: 均值%.1f  极差%.1f' % (np.mean(v), max(v)-min(v)))
    print('最细:', min(meds, key=lambda x: x[1]), ' 最粗:', max(meds, key=lambda x: x[1]))