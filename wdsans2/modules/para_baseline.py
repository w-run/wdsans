#!/usr/bin/env python3
"""para_baseline - 中英混排基线对齐测试

动机: 此前所有测量都是单字形。用户实际看到的是一整段中英混排文本。
      若拉丁与汉字基线不一致，混排会「上下跳」。

测项（400 档，四字体对比）:
  1. 汉字底线 y vs 拉丁底线 y（应一致）
  2. 汉字顶线 y vs 拉丁大写顶线 y
  3. 数字高度与汉字高度关系
  4. 混排行的墨迹包络是否平稳（逐 x 列的最高/最低墨点）
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}
SZ = 400

def render_line(path, text, px=SZ):
    ft = ImageFont.truetype(path, px)
    img = Image.new("L", (px*len(text)+200, px*3), 0)
    ImageDraw.Draw(img).text((50, px), text, fill=255, font=ft)
    return np.array(img) > 128

def bbox(bm):
    r = np.where(bm.any(axis=1))[0]; c = np.where(bm.any(axis=0))[0]
    if not len(r): return None
    return r[0], r[-1], c[0], c[-1]

def per_char_bbox(path, chars, px=SZ):
    """逐字渲染取 bbox（避免字距影响）"""
    out = {}
    for ch in chars:
        bm = render_line(path, ch, px)
        b = bbox(bm)
        if b: out[ch] = b
    return out

print("=== 单字上下边界（400px 渲染，y 向下增大）===")
print()
TEST = "永国体中HAMB0123"
for name, path in FONTS.items():
    d = per_char_bbox(path, TEST)
    if not d: 
        print("%s 无数据" % name); continue
    print("[%s]" % name)
    print("  %-4s %6s %6s %6s" % ("字", "顶", "底", "高"))
    for ch in TEST:
        if ch not in d: continue
        t, b, l, r = d[ch]
        print("  %-4s %6d %6d %6d" % (ch, t, b, b-t))
    # 对比汉字与拉丁底线
    cjk = [d[c] for c in "永国体中" if c in d]
    lat = [d[c] for c in "HAM" if c in d]
    num = [d[c] for c in "0123" if c in d]
    if cjk and lat:
        print("  -> 汉字底线均值 %.1f / 拉丁底线均值 %.1f / 差 %+.1f" % (
            np.mean([b for _,b,_,_ in cjk]),
            np.mean([b for _,b,_,_ in lat]),
            np.mean([b for _,b,_,_ in lat]) - np.mean([b for _,b,_,_ in cjk])))
    if cjk and num:
        print("  -> 汉字底线均值 %.1f / 数字底线均值 %.1f / 差 %+.1f" % (
            np.mean([b for _,b,_,_ in cjk]),
            np.mean([b for _,b,_,_ in num]),
            np.mean([b for _,b,_,_ in num]) - np.mean([b for _,b,_,_ in cjk])))
    print()

print("=== 混排行墨迹包络（逐 x 列顶/底，看是否平稳）===")
LINE = "汉字Typography混排ABC测试123"
for name, path in FONTS.items():
    bm = render_line(path, LINE)
    b = bbox(bm)
    if not b: continue
    t, bb, l, r = b
    sub = bm[t:bb+1, l:r+1]
    tops, bots = [], []
    for x in range(sub.shape[1]):
        ys = np.where(sub[:,x])[0]
        if len(ys): 
            tops.append(ys[0]); bots.append(ys[-1])
    if not tops: continue
    # 包络波动 = 顶/底的标准差（越小越平稳）
    print("  %-5s 顶线 均值%.1f σ%.1f | 底线 均值%.1f σ%.1f | 总高 %d" % (
        name, np.mean(tops), np.std(tops), np.mean(bots), np.std(bots), bb-t))
