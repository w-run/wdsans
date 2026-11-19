#!/usr/bin/env python3
"""ui_scenario - 模拟手机 UI 场景，四字体对比小字号观感"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [
    ("本字体", "/workspace/static/wdsans/WDesignSans-VF.otf"),
    ("OPPO",   "/workspace/wdsans/ref/ops/ops-400.ttf"),
    ("HOS",    "/workspace/wdsans/ref/hos/hos-400.ttf"),
    ("SHS",    "/workspace/wdsans/ref/shs/shs-400.otf"),
]

UI_ROWS = [
    "设置",
    "无线局域网   已连接",
    "蓝牙   未开启",
    "蜂窝网络   5G",
    "个人热点   关闭",
    "通用   关于本机",
    "辅助功能   显示与亮度",
]

SIZES = [12, 14, 16]
PAD = 20

for px in SIZES:
    print("=== %dpx ===" % px)
    print("%-8s %10s %10s %10s" % ("字体", "行高px", "7行总高", "行高/字号"))
    print("-" * 44)
    for name, path in FONTS:
        ft = ImageFont.truetype(path, px)
        asc, desc = ft.getmetrics()
        lh = asc + desc
        total = lh * len(UI_ROWS)
        print("%-8s %10d %10d %10.2f" % (name, lh, total, lh/px))
    print()

print("=== 渲染 14px UI 对比图 ===")
PX = 14
SCALE = 3
W = 620
row_gap = 26
block_h = (len(UI_ROWS) * row_gap + 60) * len(FONTS) + 80
img = Image.new('RGB', (W, block_h), 'white')
d = ImageDraw.Draw(img)
try:
    lbl = ImageFont.truetype(FONTS[0][1], 16)
except Exception:
    lbl = ImageFont.load_default()

y = 20
for name, path in FONTS:
    ft = ImageFont.truetype(path, PX * SCALE)
    asc, desc = ft.getmetrics()
    lh = asc + desc
    head = '[%s]  行高 %dpx @%dpx (%.2fem)' % (name, lh//SCALE, PX, lh/SCALE/PX)
    d.text((PAD, y), head, fill='#c00', font=lbl)
    y += 26
    for row in UI_ROWS:
        d.text((PAD, y), row, fill='black', font=ft)
        y += lh
    y += 30

img.save('/workspace/wdsans2/build/ui_scenario.png')
print("已保存 %s" % (img.size,))