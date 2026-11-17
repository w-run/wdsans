#!/usr/bin/env python3
"""yan_diff - pixel-diff 眼 between R29 and SHS to locate the real defect"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

R29 = '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'
SHS = '/workspace/wdsans/ref/shs/shs-400.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
SZ = 700


def render(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    return a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]


a = render(R29, "眼")
b = render(SHS, "眼")
c = render(HOS, "眼")
print('R29 %s  SHS %s  HOS %s' % (a.shape, b.shape, c.shape))

# resize to common size
from PIL import Image as I
H, W = b.shape
def rs(x):
    return np.array(I.fromarray((x*255).astype(np.uint8)).resize((W,H), I.LANCZOS)) > 128
A, B, C = rs(a), b, rs(c)

print()
print('ink  R29=%.3f  SHS=%.3f  HOS=%.3f' % (A.mean(), B.mean(), C.mean()))
D = A & ~B
print('R29-only ink pixels: %d (%.3f%% of glyph)' % (D.sum(), D.mean()*100))

# locate where the R29-only ink is, in 4x4 grid
hh, ww = D.shape
print()
print('R29-only ink distribution (4x4 grid, % of cell):')
for r in range(4):
    row = []
    for cc in range(4):
        cell = D[r*hh//4:(r+1)*hh//4, cc*ww//4:(cc+1)*ww//4]
        row.append("%5.2f" % (cell.mean()*100))
    print("   y%d: %s" % (r, "  ".join(row)))