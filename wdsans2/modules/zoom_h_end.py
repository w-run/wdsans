#!/usr/bin/env python3
"""放大横笔/竖笔端面，看是否平切"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = [("我们","/workspace/static/wdsans/WDesignSans-VF.otf"),
         ("SHS","/workspace/wdsans/ref/shs/shs-400.otf"),
         ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),
         ("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]
PX = 1400
CH = "十"

def render(path, ch, px=PX):
    ft = ImageFont.truetype(path, px)
    W = px*2
    img = Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((px//3,px//5),ch,fill=255,font=ft)
    a = np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

tiles=[]
for lbl,p in FONTS:
    m = render(p,CH)
    if m is None: continue
    h,w = m.shape
    # 横笔右端: 右上方区域
    sub = m[:int(h*0.45), int(w*0.72):]
    im = Image.fromarray((sub*255).astype(np.uint8)).resize((500,500), Image.LANCZOS)
    tiles.append((lbl+"-横右端", im))
    # 竖笔上端: 上方中间
    sub2 = m[:int(h*0.22), int(w*0.30):int(w*0.70)]
    im2 = Image.fromarray((sub2*255).astype(np.uint8)).resize((500,500), Image.LANCZOS)
    tiles.append((lbl+"-竖上端", im2))

if tiles:
    W = 500*len(tiles); H = 540
    canvas = Image.new("RGB",(W,H),"white")
    dr = ImageDraw.Draw(canvas)
    try: lf = ImageFont.truetype("/workspace/wdsans/ref/shs/shs-400.otf", 24)
    except Exception: lf = ImageFont.load_default()
    x=0
    for lbl,im in tiles:
        canvas.paste(im.convert("RGB"),(x,40))
        dr.text((x+6,6), lbl, fill="red", font=lf)
        x+=500
    canvas.save("/workspace/wdsans2/build/h_end.png")
    print("saved", canvas.size)
