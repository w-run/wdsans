#!/usr/bin/env python3
# oppo_target_3w - OPPO bar-right target at 3 weights (oppo only has 400/500/700)
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 900; UPEM = 1000
def barright(path, ch, frac):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    H, W = sub.shape
    y = min(H-1, int(H*frac))
    xs = np.where(sub[y])[0]
    if not len(xs): return None
    return xs[-1]*(UPEM/SZ)

print("OPPO 三档横笔右缘（frac=0.13，即接近横笔中线）")
print("%-4s %-10s %-10s %-10s" % ("char","400","500","700"))
for ch in "多及力刀乃予了":
    v = [barright(p, ch, 0.13) for p in [
        "/workspace/wdsans/ref/ops/ops-400.ttf",
        "/workspace/wdsans/ref/ops/ops-500.ttf",
        "/workspace/wdsans/ref/ops/ops-700.ttf"]]
    print("%-4s %-10s %-10s %-10s" % (ch, *["%.0f" % x if x else "-" for x in v]))

print()
print("SHS 三档（对照：SHS 有拐角，值偏大属正常）")
def shs(w): return "/workspace/wdsans/ref/shs/shs-%d.otf" % w
print("%-4s %-10s %-10s %-10s" % ("char","250","400","900"))
for ch in "多及力刀乃予了":
    v = [barright(shs(w), ch, 0.13) for w in [250,400,900]]
    print("%-4s %-10s %-10s %-10s" % (ch, *["%.0f" % x if x else "-" for x in v]))