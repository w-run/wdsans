#!/usr/bin/env python3
# pie_start - 撇在横笔下缘处的起点 x 位置: OPPO vs ours
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 1200; UPEM = 1000

def ink(path, ch):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def analyze(path, lbl, ch="多"):
    a = ink(path, ch)
    H, W = a.shape
    # 找横笔的上缘和下缘：横笔是最上面那个长横
    # 逐行统计墨迹宽度，横笔区域宽度大
    widths = np.array([np.where(a[y])[0] for y in range(H)], dtype=object)
    w = np.array([len(x) if len(x) else 0 for x in widths])
    # 从最右边找横笔：右缘 x
    right = np.array([x[-1] if len(x) else -1 for x in widths])
    # 横笔下缘 = 右缘开始大幅左移的位置
    d = np.diff(right.astype(int))
    drop = None
    for y in range(5, H//2):
        if d[y] <= -4:
            drop = y; break
    print("%s  W=%d H=%d" % (lbl, W, H))
    if drop is None:
        print("  no drop"); print(); return
    print("  横笔下缘 y=%d (y/H=%.2f)" % (drop, drop/H))
    print("  横笔右缘 x=%d (x/W=%.2f)" % (right[drop-1], right[drop-1]/W))
    # 下缘下一行的墨段范围
    for dy in [1, 3, 8, 15]:
        y = drop + dy
        if y < H and len(widths[y]):
            xs = widths[y]
            print("    y+%2d 行墨段 x[%d,%d]  宽%d  (右端 x/W=%.2f)" % (
                dy, xs[0], xs[-1], len(xs), xs[-1]/W))
    print()

analyze("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO400")
analyze("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", "R31-400")
analyze("/workspace/wdsans2/build/plan1b/B_400.otf", "P1b-400")