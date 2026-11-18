#!/usr/bin/env python3
# find_fat - 找 250档撇下半段变粗的位置, 逐行测厚度
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ = 2000; UPEM = 1000

def ink(path):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "多", fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def report(path, lbl):
    a = ink(path)
    T = ndimage.distance_transform_edt(a)*2
    H, W = a.shape
    k = UPEM/SZ
    print("=== %s (H=%d) ===" % (lbl, H))
    print("  y%%   最右墨段  切宽   局部厚度  (em)")
    for pct in range(4, 34, 3):
        y = int(H*pct/100)
        xs = np.where(a[y])[0]
        if not len(xs):
            print("  %-4d (空)" % pct); continue
        runs=[]; st=xs[0]; pv=xs[0]
        for x in xs[1:]:
            if x-pv>2: runs.append((st,pv)); st=x
            pv=x
        runs.append((st,pv))
        x0,x1 = runs[-1]
        th = T[y, x0:x1+1].max()
        print("  %-4d [%4d-%4d] %-6.0f %.0f" % (pct, x0, x1, (x1-x0+1)*k, th*k))
    print()

report("/workspace/wdsans/ref/shs/shs-250.otf", "SHS-250")
report("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf", "R32-250")
report("/workspace/wdsans2/build/masters_R31/master-ExtraLight-250.otf", "R31-250")