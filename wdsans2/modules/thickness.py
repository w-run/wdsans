#!/usr/bin/env python3
# thickness - 用距离变换测局部笔画厚度 (medial axis 半径 x2)
# 不依赖轮廓结构, 对所有字体通用
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ = 2000; UPEM = 1000

def ink(path, ch="多"):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def thick_map(a):
    """每个墨点到最近背景的距离 x2 = 局部笔画厚度"""
    return ndimage.distance_transform_edt(a) * 2

def analyze(path, lbl):
    a = ink(path)
    T = thick_map(a)
    H, W = a.shape
    k = UPEM / SZ
    # 横笔厚: 取上部横笔区域(最大宽墨段)的中心行的厚度峰值
    bar_th = None
    for y in range(int(H*0.05), int(H*0.25)):
        xs = np.where(a[y])[0]
        if not len(xs): continue
        runs = []
        st = xs[0]; pv = xs[0]
        for x in xs[1:]:
            if x-pv > 2: runs.append((st,pv)); st=x
            pv = x
        runs.append((st,pv))
        if len(runs)==1 and (runs[0][1]-runs[0][0]) > W*0.45:
            bar_th = T[y].max()
            break
    if bar_th is None:
        print("%-10s 找不到横笔" % lbl); return
    # 撇厚: 在横笔下方 5%~15% 高度区间, 取最右侧墨块的厚度峰值
    ds = []
    for frac in [0.06, 0.10, 0.14, 0.18]:
        y = int(H*frac)
        if y >= H: continue
        xs = np.where(a[y])[0]
        if not len(xs): continue
        runs = []; st=xs[0]; pv=xs[0]
        for x in xs[1:]:
            if x-pv > 2: runs.append((st,pv)); st=x
            pv = x
        runs.append((st,pv))
        x0, x1 = runs[-1]
        ds.append(T[y, x0:x1+1].max())
    if not ds:
        print("%-10s 无撇" % lbl); return
    diag = sum(ds)/len(ds)
    print("%-10s bar=%.0f em  diag=%s  ratio=%.2f" % (
        lbl, bar_th*k, "/".join("%.0f"%(d*k) for d in ds), diag/bar_th))

print("局部厚度比 (撇/横笔), 距离变换法:")
print("-- SHS 基准 --")
for w in [250, 400, 900]:
    analyze("/workspace/wdsans/ref/shs/shs-%d.otf" % w, "SHS-%d" % w)
print("-- 我们 R32 --")
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
for w in [250,400,900]:
    analyze("/workspace/wdsans2/build/masters_R32/"+FN[str(w)], "R32-%d" % w)
print("-- OPPO --")
for w in [400, 700]:
    analyze("/workspace/wdsans/ref/ops/ops-%d.ttf" % w, "OPPO-%d" % w)