#!/usr/bin/env python3
# zuo_ink - 「昨」的日旁 vs 右侧「乍」, 判断是否真的没居中
# 用位图看实际形态
import numpy as np
from PIL import Image, ImageDraw, ImageFont

SZ = 1200; UPEM=1000
def ink(path, ch):
    ft=ImageFont.truetype(path, SZ)
    img=Image.new("L",(SZ*2,SZ*2),0)
    ImageDraw.Draw(img).text((SZ//4,SZ//4), ch, fill=255, font=ft)
    a=np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def analyze(path,lbl):
    a=ink(path,"昨")
    H,W=a.shape
    # 找左半区和右半区的墨迹 y 范围
    half=W//2
    L=a[:,:half]; R=a[:,half:]
    ly=np.where(L.any(axis=1))[0]; ry=np.where(R.any(axis=1))[0]
    k=UPEM/SZ
    print("%-6s 左偏旁 y[%.0f,%.0f] 中心%.0f | 右主体 y[%.0f,%.0f] 中心%.0f | 差%+.0f" % (
        lbl, ly[0]*k,ly[-1]*k,(ly[0]+ly[-1])/2*k,
        ry[0]*k,ry[-1]*k,(ry[0]+ry[-1])/2*k,
        ((ly[0]+ly[-1])-(ry[0]+ry[-1]))/2*k))

analyze("/workspace/wdsans2/build/masters_R32/master-Regular-400.otf","R32")
analyze("/workspace/wdsans/ref/shs/shs-400.otf","SHS")
analyze("/workspace/wdsans/ref/ops/ops-400.ttf","OPPO")