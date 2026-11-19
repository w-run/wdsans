#!/usr/bin/env python3
"""taper_convexity - 端面凹凸性（内凹 vs 平直）"""
"""

放大图显示: 我们/SHS 端面下缘内凹，OPPO/HOS 平直。
量化: 取端面（沿笔画方向最外 15%），计算边界的
      「凸包面积 / 实际面积」-> 内凹时明显 >1。

"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

FONTS = [
    ("我们", "/workspace/static/wdsans/WDesignSans-VF.otf"),
    ("SHS", "/workspace/wdsans/ref/shs/shs-400.otf"),
    ("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf"),
    ("HOS", "/workspace/wdsans/ref/hos/hos-400.ttf"),
]
PX = 1200
CHARS = ['大', '人', '天', '夫']

def render(path, ch, px=PX):
    ft = ImageFont.truetype(path, px)
    W = px * 2
    img = Image.new('L', (W, W), 0)
    ImageDraw.Draw(img).text((px//2, px//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    cols = np.where(a.any(axis=0))[0]
    if not len(rows) or not len(cols):
        return None
    return a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]

def end_convexity(mask):
    h, w = mask.shape
    y0, x0 = int(h*0.55), int(w*0.50)
    sub = mask[y0:, x0:]
    pts = np.argwhere(sub)
    if len(pts) < 300:
        return None
    c = pts.mean(axis=0)
    d = pts - c
    cov = d.T.dot(d)/len(pts)
    ev, evec = np.linalg.eigh(cov)
    main = evec[:, np.argmax(ev)]
    if main[0] < 0:
        main = -main
    t = d.dot(main)
    tmax = float(t.max())
    span = float(t.max()-t.min())
    # 端面 = 最后 18%
    sel = pts[t >= tmax - span*0.18]
    if len(sel) < 50:
        return None
    area = float(len(sel))
    if len(sel) >= 4:
        try:
            hull = ConvexHull(sel)
            hull_area = float(hull.volume)
        except Exception:
            return None
    else:
        return None
    if hull_area <= 0:
        return None
    return dict(area=area, hull=hull_area, ratio=hull_area/area, n=len(sel))

print("=== 笔画端面凸包/实际面积比 ===")
print("  1.00 = 完全凸（平切）；>1.15 = 明显内凹")

print("%-4s %-6s %8s %8s %8s  %s" % ("字","字体","实际","凸包","比值","判定"))
print("-" * 62)
ACC = {}
for ch in CHARS:
    for lbl, p in FONTS:
        m = render(p, ch)
        if m is None:
            continue
        r = end_convexity(m)
        if r is None:
            print("%-4s %-6s 无数据" % (ch, lbl))
            continue
        ra = r['ratio']
        if ra < 1.10:
            v = "平切"
        elif ra < 1.20:
            v = "微凹"
        else:
            v = "内凹"
        print("%-4s %-6s %8.0f %8.0f %8.3f  %s" % (
            ch, lbl, r['area'], r['hull'], ra, v))
        ACC.setdefault(lbl, []).append(ra)
    print()

print("=== 汇总凸包比均值 ===")
for lbl, _ in FONTS:
    v = ACC.get(lbl)
    if v:
        print("  %-6s %.3f  (%d 字)" % (lbl, float(np.mean(v)), len(v)))