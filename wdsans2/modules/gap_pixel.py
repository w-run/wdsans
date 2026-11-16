#!/usr/bin/env python3
"""gap_pixel - 像素级判定：缝隙是否真的可���

方法: 在高分辨率下渲染单字，检查「缝隙位置」是否存在
从字内部到外部的白色连通路径（即真正的发丝裂缝）。
用 flood fill 从字形外部注入，看能否渗到内部。
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OURS = '/workspace/static/wdsans/WDesignSans-VF.otf'
FONTS = [('我们', OURS),
         ('HOS',  '/workspace/wdsans/ref/hos/hos-400.ttf'),
         ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf')]

SIZE = 800


def render(path, ch, size=SIZE):
    ft = ImageFont.truetype(path, size)
    img = Image.new("L", (size * 2, size * 2), 0)
    ImageDraw.Draw(img).text((size // 3, size // 3), ch, fill=255, font=ft)
    return np.array(img) > 128


def count_white_regions(a):
    """数白色连通区域（4-邻域）。字形越「碎」区域越多。"""
    from collections import deque
    h, w = a.shape
    seen = np.zeros_like(a, dtype=bool)
    n = 0
    for y in range(h):
        for x in range(w):
            if a[y, x] and not seen[y, x]:
                n += 1
                q = deque([(y, x)])
                seen[y, x] = True
                while q:
                    cy, cx = q.popleft()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < h and 0 <= nx < w and a[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
    return n


CAND = [('靡', 15, 17), ('廖', 0, 12), ('签', 0, 8), ('窘', 5, 7),
        ('熔', 9, 11), ('赊', 0, 5), ('秩', 1, 9), ('窝', 7, 8),
        ('滁', 8, 9), ('愉', 7, 11), ('臆', 4, 16), ('敝', 1, 9),
        ('捧', 3, 8), ('爵', 14, 15)]

print('=== 白色连通区域数（越多说明笔画越碎）===')
print('%-4s %-8s %-8s %-8s' % ('字', '我们', 'HOS', 'SHS'))
regress = 0
for ch, i, j in CAND:
    vals = []
    for lbl, p in FONTS:
        try:
            a = render(p, ch)
            vals.append(count_white_regions(a))
        except Exception:
            vals.append(None)
    flag = ''
    if vals[0] is not None and vals[2] is not None and vals[0] > vals[2]:
        flag = '  <<< 我们更碎'
        regress += 1
    print('%-4s %-8s %-8s %-8s%s' % (ch, vals[0], vals[1], vals[2], flag))
print()
print('我们区域数多于 SHS 的字: %d/%d' % (regress, len(CAND)))