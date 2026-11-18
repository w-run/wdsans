#!/usr/bin/env python3
# target_x - what bar right-x does OPPO use vs ours, per weight, several chars
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 900; UPEM = 1000

def barright(path, ch, frac):
    """rightmost ink in the row at given fraction from glyph top"""
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    cols = np.where(a.any(axis=0))[0]
    sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    H, W = sub.shape
    y = min(H-1, int(H*frac))
    xs = np.where(sub[y])[0]
    if not len(xs): return None, None
    k = UPEM / SZ
    return xs[-1]*k, W*k

OP = "/workspace/wdsans/ref/ops/ops-400.ttf"
RN = "/workspace/wdsans2/build/masters_R31/master-Regular-400.otf"
TN = "/workspace/wdsans2/build/masters_T6/master-Regular-400.otf"

print("%-4s %-6s %-10s %-10s %-10s %s" % ("char","frac","OPPO","R31","T6","R31/OPPO"))
for ch in "多及力刀乃予":
    for frac in [0.13, 0.18, 0.24]:
        o, ow = barright(OP, ch, frac)
        r, rw = barright(RN, ch, frac)
        t, tw = barright(TN, ch, frac)
        ratio = ("%.2f" % (r/o)) if (o and r) else "-"
        print("%-4s %-6.2f %-10s %-10s %-10s %s" % (ch, frac,
            "%.0f" % o if o else "-", "%.0f" % r if r else "-",
            "%.0f" % t if t else "-", ratio))
    print()