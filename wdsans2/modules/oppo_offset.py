#!/usr/bin/env python3
# oppo_offset - 多个字上测 OPPO 左偏旁相对右主体的垂直偏移, 求稳定值
# 只看左右结构 + 左偏旁是封闭方框(口/日/囗/田/目)的字
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 1600; UPEM = 1000

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def split_center(a, frac=0.50):
    """左半/右半 的墨迹垂直中心"""
    H, W = a.shape
    cut = int(W*frac)
    L = a[:, :cut]; R = a[:, cut:]
    ly = np.where(L.any(axis=1))[0]; ry = np.where(R.any(axis=1))[0]
    if not len(ly) or not len(ry): return None
    return (ly[0]+ly[-1])/2.0, (ry[0]+ry[-1])/2.0, H

def measure(path, lbl, chars):
    print("=== %s ===" % lbl)
    print("  ch   leftC  rightC   diff(em)")
    ds = []
    k = UPEM/SZ
    for ch in chars:
        try:
            a = ink(path, ch)
        except Exception:
            continue
        if a is None: continue
        r = split_center(a)
        if r is None: continue
        lc, rc, H = r
        # 以字面高度归一化到 1000 upem
        sc = UPEM / H
        d = (lc - rc) * sc
        ds.append(d)
        print("  %s   %5.0f  %5.0f   %+6.0f" % (ch, lc*sc, rc*sc, d))
    if ds:
        ds.sort()
        print("  --> 中位 %.0f  均值 %.0f  范围 [%.0f, %.0f]  (n=%d)" % (
            ds[len(ds)//2], sum(ds)/len(ds), ds[0], ds[-1], len(ds)))
    print()
    return ds

CH = "昨晴暗晚旺昧昭昕晌晖明暗昨"
CH2 = "昨晴暗晚旺昧昭昕晌晖"
O = "/workspace/wdsans/ref/ops/ops-400.ttf"
S = "/workspace/wdsans/ref/shs/shs-400.otf"
R = "/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"
measure(O, "OPPO-400", CH2)
measure(S, "SHS-400", CH2)
measure(R, "R32-400", CH2)