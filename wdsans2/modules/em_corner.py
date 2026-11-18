#!/usr/bin/env python3
# em_corner - OPPO corner in em units vs ours
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 900; UPEM = 1000

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def corner(path, lbl, ch="多"):
    a = ink(path, ch)
    H, W = a.shape
    k = UPEM/SZ
    # 逐行右缘
    prof = np.array([np.where(a[y])[0][-1] if a[y].any() else -1 for y in range(H)])
    # 找右缘第一次开始下降的行（拐角起点）
    d = np.diff(prof.astype(int))
    start = None
    for y in range(int(H*0.05), int(H*0.5)):
        if d[y] <= -2:
            start = y; break
    print("%s: bmp %dx%d" % (lbl, W, H))
    if start:
        print("   右缘开始下降 y=%d px (em %.0f)  x=%.0f px (em %.0f)" % (
            start, start*k, prof[start], prof[start]*k))
        print("   下降前平台长度: %d 行 = %.0f em" % (start, start*k))
        # 下降段斜率
        seg = d[start:min(start+40, len(d))]
        print("   下降段 40 行总位移: %d px = %.0f em" % (int(seg.sum()), seg.sum()*k))
    print()

corner("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO 400")
corner("/workspace/wdsans2/build/masters_T6/master-Regular-400.otf", "T6  400")
corner("/workspace/wdsans2/build/plan1b/B_400.otf", "P1b 400")
corner("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", "R31 400")