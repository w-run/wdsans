#!/usr/bin/env python3
# base_measure - 用位图法(不依赖轮廓分割)测左半区墨迹的垂直范围
# 对比 R32 / SHS / OPPO, 找出稳定的高度差和中心差
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

def left_band(path, ch, frac=0.42):
    """左 42% 区域墨迹的 y 范围, 归一化到 1000 upem"""
    a = ink(path, ch)
    if a is None: return None
    H, W = a.shape
    cut = int(W*frac)
    L = a[:, :cut]
    ys = np.where(L.any(axis=1))[0]
    if not len(ys): return None
    sc = UPEM/H
    y0 = ys[0]*sc; y1 = ys[-1]*sc
    return y0, y1, y1-y0, (y0+y1)/2

O="/workspace/wdsans/ref/ops/ops-400.ttf"
S="/workspace/wdsans/ref/shs/shs-400.otf"
R="/workspace/wdsans2/build/masters_R32/master-Regular-400.otf"

CH="叫叨叩叶叹叽叼叭叮叱昨晴暗晚旺昧昭昕晌晖"
print("左半区墨迹垂直范围 (em, 归一化):")
print("%-2s | %-22s | %-22s | %-22s" % ("ch","R32 我们","SHS","OPPO"))
print("-"*76)
rows=[]
for ch in CH:
    a = left_band(R, ch); b = left_band(S, ch); c = left_band(O, ch)
    if not a: continue
    fmt = lambda t: "[%4.0f,%4.0f] 高%3.0f" % (t[0],t[1],t[2]) if t else "        --      "
    print("%-2s | %-22s | %-22s | %-22s" % (ch, fmt(a), fmt(b), fmt(c)))
    if b and c: rows.append((ch, a, b, c))
print()
if rows:
    dh = [ (a[2]-b[2]) for ch,a,b,c in rows ]
    dc = [ (a[3]-b[3]) for ch,a,b,c in rows ]
    print("我们 vs SHS:  高度差 中位 %.0f  中心差 中位 %.0f" % (np.median(dh), np.median(dc)))
    dh2 = [ (b[2]-c[2]) for ch,a,b,c in rows ]
    dc2 = [ (b[3]-c[3]) for ch,a,b,c in rows ]
    print("SHS  vs OPPO: 高度差 中位 %.0f  中心差 中位 %.0f" % (np.median(dh2), np.median(dc2)))