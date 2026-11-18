#!/usr/bin/env python3
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ = 2000; UPEM = 1000
def ink(path):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "多", fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def rep(path, lbl):
    try: a = ink(path)
    except Exception as e: print("%-16s ERR" % lbl); return
    T = ndimage.distance_transform_edt(a)*2
    H, W = a.shape; k = UPEM/SZ
    vals=[]
    for pct in [16,19,22,25,28,31]:
        y=int(H*pct/100); xs=np.where(a[y])[0]
        if not len(xs): vals.append(None); continue
        runs=[]; st=xs[0]; pv=xs[0]
        for x in xs[1:]:
            if x-pv>2: runs.append((st,pv)); st=x
            pv=x
        runs.append((st,pv))
        x0,x1=runs[-1]
        vals.append(T[y,x0:x1+1].max()*k)
    print("%-16s " % lbl + "  ".join("%.0f"%v if v else "-" for v in vals))

print("撇厚度 (y=16%~31%):")
rep("/workspace/wdsans/ref/shs/shs-250.otf", "SHS-250 基准")
rep("/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf", "T6-250")
rep("/workspace/wdsans2/build/masters_R32/master-ExtraLight-250.otf", "R32-250 现在")
rep("/workspace/wdsans2/build/fix3/A_250.otf", "fix3A-250 新")