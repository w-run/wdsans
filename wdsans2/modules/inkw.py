#!/usr/bin/env python3
# inkw - 按 y 高度测墨宽（不依赖轮廓结构），三字体三档
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 1600; UPEM = 1000

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def barh(a):
    """横笔厚度: 顶部区域逐行墨宽最大的连续带"""
    H, W = a.shape
    # 取最上面 25% 区域
    wid = np.array([a[y].sum() for y in range(H)])
    top = int(H*0.02); lim = int(H*0.28)
    # 横笔区域: 墨宽 > 60% 宽度的行
    sel = [y for y in range(top, lim) if wid[y] > W*0.55]
    if not sel: return None, None, None
    return len(sel), sel[0], sel[-1]

def diagw(a, yfrac):
    """在指定高度, 取最右侧墨段的宽度(撇的垂直切宽)"""
    H, W = a.shape
    y = int(H*yfrac)
    xs = np.where(a[y])[0]
    if not len(xs): return None
    runs = []
    st = xs[0]; pv = xs[0]
    for x in xs[1:]:
        if x - pv > 2:
            runs.append(pv-st+1); st = x
        pv = x
    runs.append(pv-st+1)
    return runs[-1]

def report(path, lbl):
    a = ink(path, "多")
    H, W = a.shape
    k = UPEM/SZ
    # 横笔厚: 用像素行数
    n, y0, y1 = barh(a)
    if n is None:
        print("%-10s 未检出横笔" % lbl); return
    bar_px = n
    out = ["%-10s bar=%.0f em" % (lbl, bar_px*k)]
    for yf in [0.20, 0.24, 0.28]:
        d = diagw(a, yf)
        if d:
            out.append("y%.0f%%:%.2f" % (yf*100, d/bar_px))
    print("  ".join(out))

S = "/workspace/wdsans/ref/shs/shs-%d.otf"
R32 = "/workspace/wdsans2/build/masters_R32/"; T6 = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OP = "/workspace/wdsans/ref/ops/ops-400.ttf"
print("撇垂直切宽 / 横笔厚  (越小=撇越细)")
for w in [250, 400, 900]:
    report(S % w, "SHS-%d" % w)
print()
for w in [250, 400, 900]:
    report(R32+FN[str(w)], "R32-%d" % w)
print()
report(OP, "OPPO-400")