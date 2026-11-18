#!/usr/bin/env python3
# render_vf - 直接渲染部署的 VF, 三档 多 的拐角
import sys, io
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFont

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
SZ = 900
for w in [250, 400, 900]:
    f = TTFont(VF)
    f = instantiateVariableFont(f, {"wght": w}, inplace=True)
    buf = io.BytesIO(); f.save(buf); f.close(); buf.seek(0)
    ft = ImageFont.truetype(buf, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 255)
    ImageDraw.Draw(img).text((SZ//3, SZ//3), "多", fill=0, font=ft)
    # 裁右上角区域
    a = np.array(img) < 128
    rows = np.where(a.any(axis=1))[0]; cols = np.where(a.any(axis=0))[0]
    sub = a[rows[0]:rows[-1]+1, cols[0]:cols[-1]+1]
    H, W = sub.shape
    crop = sub[int(H*0.10):int(H*0.30), int(W*0.70):]
    out = Image.fromarray((~crop * 255).astype(np.uint8)).resize((crop.shape[1]*4, crop.shape[0]*4), Image.NEAREST)
    out.save("/workspace/wdsans2/build/vfc_%d.png" % w)
    print("  wght %d saved vfc_%d.png" % (w, w))