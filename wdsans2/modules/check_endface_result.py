#!/usr/bin/env python3
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

FONTS = [
    ("我们-改前", "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"),
    ("我们-改后", "/workspace/wdsans2/build/test_endface.otf"),
    ("OPPO", "/workspace/wdsans/ref/ops/ops-400.ttf"),
    ("HOS", "/workspace/wdsans/ref/hos/hos-400.ttf"),
]
PX = 1200
CHARS = ["大","人","天","夫","文","父"]

def render(path, ch, px=PX):
    ft = ImageFont.truetype(path, px)
    W = px*2
    img = Image.new("L", (W,W), 0)
    ImageDraw.Draw(img).text((px//2, px//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def convexity(mask):
    h,w = mask.shape
    y0,x0 = int(h*0.55), int(w*0.50)
    sub = mask[y0:, x0:]
    pts = np.argwhere(sub)
    if len(pts) < 300: return None
    c = pts.mean(axis=0); d = pts - c
    cov = d.T.dot(d)/len(pts)
    ev, evec = np.linalg.eigh(cov)
    main = evec[:, np.argmax(ev)]
    if main[0] < 0: main = -main
    t = d.dot(main)
    tmax = float(t.max()); span = float(t.max()-t.min())
    sel = pts[t >= tmax - span*0.18]
    if len(sel) < 50: return None
    try:
        hull = ConvexHull(sel)
        return float(hull.volume)/float(len(sel))
    except Exception:
        return None

print("=== 端面凸包比（1.00=平切, >1.02=内凹）===")
print("%-4s %-10s %8s  %s" % ("字","字体","凸包比","判定"))
print("-" * 44)
ACC = {}
for ch in CHARS:
    for lbl, p in FONTS:
        m = render(p, ch)
        if m is None: continue
        r = convexity(m)
        if r is None: continue
        v = "平切" if r < 1.010 else ("近直" if r < 1.020 else "内凹")
        print("%-4s %-10s %8.3f  %s" % (ch, lbl, r, v))
        ACC.setdefault(lbl, []).append(r)
    print()
print("=== 汇总 ===")
for lbl, _ in FONTS:
    v = ACC.get(lbl)
    if v:
        print("  %-10s %.3f  (%d 字)" % (lbl, float(np.mean(v)), len(v)))
