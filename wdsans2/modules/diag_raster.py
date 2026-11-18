#!/usr/bin/env python3
"""diag_raster - 确认碎裂是栅格化效应而非字形缺陷

思路: 若碎裂是栅格化效应，那么把字号放大到 16 的整数倍再缩小回 16px 等效分辨率，
      碎裂应当消失或大幅减少（因为反锯齿会填充原本的亚像素间隙）。

对比三种渲染:
  A. 直接 16px
  B. 128px 渲染后 8x 降采样到 16px 等效
  C. 全文抗锯齿（256px -> 64px -> 16px）
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

F = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
}

def direct(path, ch, px):
    ft = ImageFont.truetype(path, px)
    img = Image.new("L", (px*4, px*4), 0)
    ImageDraw.Draw(img).text((px//2, px//2), ch, fill=255, font=ft)
    return np.array(img)

def supersample(path, ch, px, factor):
    big = px * factor
    ft = ImageFont.truetype(path, big)
    img = Image.new("L", (big*4, big*4), 0)
    ImageDraw.Draw(img).text((big//2, big//2), ch, fill=255, font=ft)
    a = np.array(img)
    # 裁到墨迹再降采样
    r = np.where((a>10).any(axis=1))[0]; c = np.where((a>10).any(axis=0))[0]
    if not len(r): return None
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    h, w = a.shape
    nh, nw = max(1, h//factor), max(1, w//factor)
    im = Image.fromarray(a).resize((nw, nh), Image.LANCZOS)
    return np.array(im)

def blocks(bm, thr=128):
    if bm is None: return None
    a = bm > thr
    if not a.any(): return None
    return int(ndimage.label(a)[1])

print("=== 三种渲染方式下的块数对比（16px 等效）===")
print("%-4s %6s | %-18s | %-18s" % ("字", "", "直接16px", "8x超采样"))
print("%-4s %6s | %6s %6s | %6s %6s" % ("", "", "我们", "SHS", "我们", "SHS"))
print("-" * 56)
for ch in ("数", "边", "全", "今", "政", "京", "以", "这"):
    d_a = blocks(direct(F["我们"], ch, 16))
    d_b = blocks(direct(F["SHS"], ch, 16))
    s_a = blocks(supersample(F["我们"], ch, 16, 8))
    s_b = blocks(supersample(F["SHS"], ch, 16, 8))
    print("%-4s %6s | %6s %6s | %6s %6s" % (
        ch, "", d_a, d_b, s_a, s_b))

print()
print("=== 阈值敏感性（直接 16px，不同二值化阈值）===")
print("%-4s | %-24s | %-24s" % ("", "我们", "SHS"))
print("%-4s | %6s %6s %6s | %6s %6s %6s" % ("字", "t=64", "t=128", "t=192", "t=64", "t=128", "t=192"))
for ch in ("数", "边", "全", "今"):
    row = [ch]
    for t in (64, 128, 192):
        row.append(blocks(direct(F["我们"], ch, 16), t))
    for t in (64, 128, 192):
        row.append(blocks(direct(F["SHS"], ch, 16), t))
    print("%-4s | %6s %6s %6s | %6s %6s %6s" % tuple(row))
