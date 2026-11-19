#!/usr/bin/env python3
"""line_height_test - 实测多行文本的行距"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = {
    "我们": "/workspace/static/wdsans/WDesignSans-VF.otf",
    "SHS":  "/workspace/wdsans/ref/shs/shs-400.otf",
    "OPPO": "/workspace/wdsans/ref/ops/ops-400.ttf",
    "HOS":  "/workspace/wdsans/ref/hos/hos-400.ttf",
}
PX = 100
TEXT = "第一行文字\n第二行文字\n第三行文字"

def render_lines(path, px=PX):
    ft = ImageFont.truetype(path, px)
    lines = TEXT.split(chr(10))
    # 逐行渲染，用 font metrics 计算基线间距
    asc, desc = ft.getmetrics()
    line_h = asc + desc
    W = px * 6
    H = line_h * len(lines) + px
    img = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(img)
    ys = []
    for i, ln in enumerate(lines):
        y = i * line_h
        d.text((10, y), ln, fill=255, font=ft)
        ys.append(y)
    a = np.array(img) > 128
    rows = np.where(a.any(axis=1))[0]
    if not len(rows): return None
    return dict(line_h=line_h, asc=asc, desc=desc,
                ink_h=rows[-1]-rows[0]+1, total_h=H)

print("%-6s %8s %8s %8s %10s %10s" % ("字体","line_h","asc","desc","行高/字号","墨迹总高"))
print("-" * 62)
res = {}
for name, path in FONTS.items():
    r = render_lines(path)
    if not r:
        print("%-6s 渲染失败" % name); continue
    res[name] = r
    print("%-6s %8d %8d %8d %10.2f %10d" % (
        name, r['line_h'], r['asc'], r['desc'], r['line_h']/PX, r['ink_h']))

print()
print("=== 相对我们的行高比例 ===")
if '我们' in res:
    base = res['我们']['line_h']
    for name in FONTS:
        if name in res:
            print("  %-6s %d  (%.3f x 我们)" % (name, res[name]["line_h"], res[name]["line_h"]/base))