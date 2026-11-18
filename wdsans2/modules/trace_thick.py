#!/usr/bin/env python3
# trace_thick - 逐阶段测 250档「多」的撇厚, 找哪一步变粗
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
import os

SZ=2000; UPEM=1000
def thick(path):
    if not os.path.exists(path): return None
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "多", fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return None
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
    return sum(vals)/len(vals) if vals else None

B="/workspace/wdsans2/build/"
STAGES = [
  ("SHS",   "/workspace/wdsans/ref/shs/shs-250.otf"),
  ("T6",    B+"masters_T6/master-ExtraLight-250.otf"),
  ("MOD",   B+"masters_MOD/master-ExtraLight-250.otf"),
  ("R1",    B+"masters_R1/master-ExtraLight-250.otf"),
  ("R4",    B+"masters_R4/master-ExtraLight-250.otf"),
  ("R15",   B+"masters_R15/master-ExtraLight-250.otf"),
  ("R29",   B+"masters_R29/master-ExtraLight-250.otf"),
  ("R30",   B+"masters_R30/master-ExtraLight-250.otf"),
  ("R31",   B+"masters_R31/master-ExtraLight-250.otf"),
  ("R32",   B+"masters_R32/master-ExtraLight-250.otf"),
  ("R33",   B+"masters_R33/master-ExtraLight-250.otf"),
  ("R34",   B+"masters_R34/master-ExtraLight-250.otf"),
]
print("%-6s %s" % ("stage","撇厚"))
prev=None
for lbl, p in STAGES:
    v = thick(p)
    if v is None:
        print("%-6s (缺失)" % lbl); continue
    d = "" if prev is None else ("  %+.0f" % (v-prev))
    print("%-6s %.0f%s" % (lbl, v, d))
    prev = v