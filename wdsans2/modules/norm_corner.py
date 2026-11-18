#!/usr/bin/env python3
# norm_corner - corner描述用字面框归一化, 消除字面率差异
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

def describe(path, lbl, ch="多"):
    a = ink(path, ch)
    H, W = a.shape
    prof = np.array([np.where(a[y])[0][-1] if a[y].any() else -1 for y in range(H)])
    # 归一化：x/W, y/H
    d = np.diff(prof.astype(int))
    # 找第一个显著下降
    start = None
    for y in range(int(H*0.05), int(H*0.6)):
        if d[y] <= -3:
            start = y; break
    print("%-10s W=%d H=%d" % (lbl, W, H))
    if start is None:
        print("   未找到拐角"); print(); return
    print("   拐角起点: y/H=%.2f  x/W=%.2f  (x=%d)" % (start/H, prof[start]/W, prof[start]))
    # 平台段（拐角前）右缘是否恒定
    plateau = prof[:start+1]
    if len(plateau) > 5:
        print("   平台右缘: min=%d max=%d 波动=%d px" % (plateau.min(), plateau.max(), plateau.max()-plateau.min()))
    # 下降斜率：每行右移多少
    seg = d[start:start+min(60, len(d)-start)]
    print("   下降段60行位移=%d px  平均 %.2f px/行" % (int(seg.sum()), seg.mean()))
    # 最右点位置
    mx = prof.max()
    my = int(np.argmax(prof))
    print("   最右点: x/W=%.2f y/H=%.2f" % (mx/W, my/H))
    print()

describe("/workspace/wdsans/ref/ops/ops-400.ttf", "OPPO400")
describe("/workspace/wdsans/ref/ops/ops-700.ttf", "OPPO700")
describe("/workspace/wdsans2/build/masters_T6/master-Regular-400.otf", "T6-400")
describe("/workspace/wdsans2/build/plan1b/B_400.otf", "P1b-400")
describe("/workspace/wdsans2/build/masters_R31/master-Regular-400.otf", "R31-400")