#!/usr/bin/env python3
# Bitmap right-edge profile: OPPO vs R31 vs T6 for 多
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 900
UPEM = 1000

def bmp(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    cols = np.where(a.any(axis=0))[0]
    return a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]

def report(path, lbl, ch):
    a = bmp(path, ch)
    H, W = a.shape
    k = UPEM / SZ
    prof = []
    for y in range(H):
        xs = np.where(a[y])[0]
        prof.append(int(xs[-1]) if len(xs) else -1)
    prof = np.array(prof)
    lo = int(H*0.10); hi = int(H*0.32)
    print("%s  bmp=%dx%d" % (lbl, W, H))
    step = max(1, (hi-lo)//10)
    for y in range(lo, hi, step):
        print("   y=%3d  x=%4d  (em %4.0f)" % (y, prof[y], prof[y]*k))
    d = np.diff(prof[lo:hi].astype(int))
    mx = int(-d.min()) if d.min() < 0 else 0
    print("   max inward step in band: %d px = %.0f em" % (mx, mx*k))
    print()

for lbl, p in [("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf"),
               ("R31 ", "/workspace/wdsans2/build/masters_R31/master-Regular-400.otf"),
               ("T6  ", "/workspace/wdsans2/build/masters_T6/master-Regular-400.otf")]:
    report(p, lbl, "多")