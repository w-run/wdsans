#!/usr/bin/env python3
# pixdiff - R31 vs R32 像素级差异, 量化到底改了什么
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 400
def render(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), ch, fill=255, font=ft)
    return np.array(img) > 128

R31 = "/workspace/wdsans2/build/masters_R31/"
R32 = "/workspace/wdsans2/build/masters_R32/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

print("R31 vs R32 像素差异 (400px 渲染):")
print("%-4s %-5s %-10s %-10s %s" % ("char","wt","diff_px","ink_R31","ink_R32"))
for ch in "多及力刀乃予勇永了夕":
    for tag in ["250","900"]:
        try:
            a = render(R31 + FN[tag], ch)
            b = render(R32 + FN[tag], ch)
        except Exception as e:
            continue
        d = int((a ^ b).sum())
        print("%-4s %-5s %-10d %-10d %d" % (ch, tag, d, a.sum(), b.sum()))
    print()