#!/usr/bin/env python3
# cmp_t6_34 - 对比 T6(未 barple) / R34(已 barple) / SHS 的撇厚
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ = 2000; UPEM = 1000
def thick(path, ch="多"):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return 0
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    T = ndimage.distance_transform_edt(a)*2
    H, W = a.shape; k = UPEM/SZ
    vals=[]
    for pct in [19,22,25,28]:
        y=int(H*pct/100); xs=np.where(a[y])[0]
        if not len(xs): continue
        runs=[]; st=xs[0]; pv=xs[0]
        for x in xs[1:]:
            if x-pv>2: runs.append((st,pv)); st=x
            pv=x
        runs.append((st,pv))
        x0,x1=runs[-1]
        vals.append(T[y,x0:x1+1].max()*k)
    return sum(vals)/len(vals) if vals else 0

FN={250:"master-ExtraLight-250.otf",400:"master-Regular-400.otf",900:"master-Heavy-900.otf"}
print("%-6s %-10s %-10s %-10s" % ("wt","T6","R34","SHS"))
for w in [250,400,900]:
    t6 = thick("/workspace/wdsans2/build/masters_T6/"+FN[w])
    r34 = thick("/workspace/wdsans2/build/masters_R34/"+FN[w])
    shs = thick("/workspace/wdsans/ref/shs/shs-%d.otf"%w)
    print("%-6d %-10.0f %-10.0f %-10.0f" % (w, t6, r34, shs))