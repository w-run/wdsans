#!/usr/bin/env python3
"""量化横笔右端面的垂直度（是否平切）"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [("我们","/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("SHS","/workspace/wdsans/ref/shs/shs-400.otf"),
         ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),
         ("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]
CHARS = ["十","一","二","三","王","干","土","士"]
PX = 1000

def render(path, ch, px=PX):
    ft = ImageFont.truetype(path, px)
    W = px*2
    img = Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((px//2,px//4),ch,fill=255,font=ft)
    a = np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def h_end_tilt(mask):
    """找横笔右端，量端面倾斜（x 随 y 的变化）"""
    h,w = mask.shape
    # 横笔: 找最宽的行，取其右端
    best_y = None; best_w = 0
    widths = []
    for y in range(h):
        row = np.where(mask[y])[0]
        if len(row)==0:
            widths.append(0); continue
        ww = row[-1]-row[0]+1
        widths.append(ww)
        if ww > best_w:
            best_w = ww; best_y = y
    if best_y is None or best_w < w*0.7:
        return None
    # 横笔纵向范围（宽度 > 85% 最宽 的行）
    band = [y for y in range(h) if widths[y] > best_w*0.85]
    if len(band) < 5:
        return None
    y0, y1 = min(band), max(band)
    if y1-y0 < 8:
        return None
    xs = []
    for y in range(y0, y1+1):
        row = np.where(mask[y])[0]
        if len(row)==0: continue
        xs.append((y, row[-1]))
    if len(xs) < 5:
        return None
    ys = np.array([p[0] for p in xs], dtype=float)
    xv = np.array([p[1] for p in xs], dtype=float)
    A = np.vstack([ys, np.ones(len(ys))]).T
    coef,_,_,_ = np.linalg.lstsq(A, xv, rcond=None)
    resid = xv - A.dot(coef)
    rms = float(np.sqrt(np.mean(resid**2)))
    tilt = float(xv.max()-xv.min())
    height = float(y1-y0+1)
    return dict(rms=rms, tilt=tilt, height=height, ratio=tilt/height if height>0 else 0)

print("=== 横笔右端面倾斜（tilt/height 越小越垂直平切）===")
print("%-4s %-6s %8s %8s %10s  %s" % ("字","字体","rms","tilt","tilt/height","判定"))
print("-"*60)
ACC={}
for ch in CHARS:
    for lbl,p in FONTS:
        m = render(p,ch)
        if m is None: continue
        r = h_end_tilt(m)
        if r is None:
            continue
        ra = r["ratio"]
        v = "垂直平切" if ra < 0.08 else ("微斜" if ra < 0.20 else "明显斜切")
        print("%-4s %-6s %8.2f %8.1f %10.3f  %s" % (ch,lbl,r["rms"],r["tilt"],ra,v))
        ACC.setdefault(lbl,[]).append(ra)
    print()
print("=== 汇总 tilt/height 均值 ===")
for lbl,_ in FONTS:
    v = ACC.get(lbl)
    if v:
        print("  %-6s %.3f  (%d 字)" % (lbl, float(np.mean(v)), len(v)))
