#!/usr/bin/env python3
"""render_r36 - 渲染 R35 vs R36 行高对比图"""
from PIL import Image, ImageDraw, ImageFont

OLD = "/workspace/static/wdsans/WDesignSans-VF.otf"
NEW = "/workspace/wdsans2/build/VF_R36.otf"

ROWS = [
    "设置",
    "无线局域网   已连接",
    "蓝牙   未开启",
    "蜂窝网络   5G",
    "个人热点   关闭",
    "通用   关于本机",
    "辅助功能   显示与亮度",
]
PX = 14
SCALE = 3
W = 620
PAD = 20

# 两种行高：R35 用 1.45em, R36 用 1.35em
VARIANTS = [
    ("R34/R35  行高 1.45em", OLD, 1.45),
    ("R36      行高 1.35em", NEW, 1.35),
    ("OPPO     参考 1.33em", "/workspace/wdsans/ref/ops/ops-400.ttf", 1.33),
    ("HOS      参考 1.19em", "/workspace/wdsans/ref/hos/hos-400.ttf", 1.19),
]

block_h = int(len(ROWS) * 1.5 * PX * SCALE + 90) * len(VARIANTS) + 60
img = Image.new('RGB', (W, block_h), 'white')
d = ImageDraw.Draw(img)
try:
    lbl = ImageFont.truetype(OLD, 15)
except Exception:
    lbl = ImageFont.load_default()

y = 20
for name, path, em in VARIANTS:
    ft = ImageFont.truetype(path, PX * SCALE)
    lh = int(em * PX * SCALE)
    d.text((PAD, y), name, fill='#c00', font=lbl)
    y += 24
    for row in ROWS:
        d.text((PAD, y), row, fill='black', font=ft)
        y += lh
    y += 24

img.save('/workspace/wdsans2/build/r36_lineheight.png')
print("saved %s" % (img.size,))