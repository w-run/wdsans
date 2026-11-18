#!/usr/bin/env python3
# struct_detect - 几何判断左右/上下结构, 带对照组验证
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 800

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def classify(path, ch):
    a = ink(path, ch)
    if a is None: return None, 0, 0
    H, W = a.shape
    col = a.any(axis=0); row = a.any(axis=1)
    lo, hi = int(W*0.25), int(W*0.75)
    gap_x = 0; cur = 0
    for x in range(lo, hi):
        if not col[x]:
            cur += 1
            if cur > gap_x: gap_x = cur
        else:
            cur = 0
    lo, hi = int(H*0.25), int(H*0.75)
    gap_y = 0; cur = 0
    for y in range(lo, hi):
        if not row[y]:
            cur += 1
            if cur > gap_y: gap_y = cur
        else:
            cur = 0
    if gap_x > gap_y*1.3: kind = "LR"
    elif gap_y > gap_x*1.3: kind = "TB"
    else: kind = "?"
    return kind, gap_x*1000.0/W, gap_y*1000.0/H

O = "/workspace/wdsans/ref/ops/ops-400.ttf"
print("对照: 左右结构 (期望 LR)")
for ch in "明昨晴晚旺昭暗昧昕晌":
    k, gx, gy = classify(O, ch)
    print("  %s -> %-3s gapX=%5.0f gapY=%5.0f" % (ch, k, gx, gy))
print()
print("对照: 上下结构 (期望 TB)")
for ch in "苜芓芒宁昱罗旨昔":
    k, gx, gy = classify(O, ch)
    print("  %s -> %-3s gapX=%5.0f gapY=%5.0f" % (ch, k, gx, gy))
print()
print("对照: 独体 (期望 ?)")
for ch in "血丫言产口日田目":
    k, gx, gy = classify(O, ch)
    print("  %s -> %-3s gapX=%5.0f gapY=%5.0f" % (ch, k, gx, gy))