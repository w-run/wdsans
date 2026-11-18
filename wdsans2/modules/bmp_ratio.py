#!/usr/bin/env python3
# bmp_ratio - 位图法测 撇/横笔 比, 覆盖 SHS/我们/OPPO
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 2000; UPEM = 1000

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def runs_at(a, y):
    xs = np.where(a[y])[0]
    if not len(xs): return []
    out = []; st = xs[0]; pv = xs[0]
    for x in xs[1:]:
        if x - pv > 2:
            out.append((st, pv, pv-st+1)); st = x
        pv = x
    out.append((st, pv, pv-st+1))
    return out

def analyze(path, lbl):
    a = ink(path, "多")
    H, W = a.shape
    k = UPEM/SZ
    # 横笔厚: 从顶部找第一个"宽墨段"的连续行数
    bar = None
    for y in range(int(H*0.01), int(H*0.30)):
        rr = runs_at(a, y)
        if not rr: continue
        # 横笔: 单段且很宽
        if len(rr) == 1 and rr[0][2] > W*0.45:
            y_top = y; break
    else:
        print("%-10s 找不到横笔起点" % lbl); return
    y_bot = y_top
    for y in range(y_top, min(H, int(H*0.35))):
        rr = runs_at(a, y)
        if len(rr) == 1 and rr[0][2] > W*0.45:
            y_bot = y
        else:
            break
    bar_px = y_bot - y_top + 1
    # 撇: 横笔下缘以下 3~8 个百分点, 取最右段宽
    ds = []
    for frac in [0.03, 0.05, 0.07]:
        y = y_bot + int(H*frac)
        if y >= H: continue
        rr = runs_at(a, y)
        if rr:
            ds.append(rr[-1][2])
    if not ds:
        print("%-10s bar=%.0fem  no diag" % (lbl, bar_px*k)); return
    avg = sum(ds)/len(ds)
    print("%-10s bar=%.0f em  diag(h)=%s em  ratio=%.2f" % (
        lbl, bar_px*k, "/".join("%.0f"%(d*k) for d in ds), avg/bar_px))

print("撇的水平切宽 / 横笔厚（位图法）:")
print("-- SHS --")
for w in [250, 400, 900]: analyze("/workspace/wdsans/ref/shs/shs-%d.otf"%w, "SHS-%d"%w)
print("-- R32 (我们当前) --")
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
for w in [250,400,900]: analyze("/workspace/wdsans2/build/masters_R32/"+FN[str(w)], "R32-%d"%w)
print("-- OPPO --")
for w in [400, 700]: analyze("/workspace/wdsans/ref/ops/ops-%d.ttf"%w, "OPPO-%d"%w)