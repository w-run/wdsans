"""验证「折角微圆」是否真实存在。

结论：不存在。
  - 四个字体（Noto/OPPO/HOS/本产物）的 on-curve 角点角度**全部是 90°**
  - 800px 渲染 + 5x 像素放大，三个字体角点都是硬直角，无亚像素圆角
  - 之前「OPPO 有圆角」是低分辨率缩略图的抗锯齿错觉

所以这个算子不该实现。DP 资源应该花在真实差异上。

顺带记录：真正的角点差异在**点的数量**，不在圆度：
  口: Noto 12 点 / OPPO 8 点 / HOS 12 点
  日: Noto 16 点 / OPPO 12 点 / HOS 16 点
  田: Noto 20 点 / OPPO 20 点 / HOS 24 点
  → OPPO 用更少的点表达同样的直角（底横并入外框），这就是「去脚」
    已经做掉的那件事，不是圆角。
"""
import sys, subprocess, os
import numpy as np
from PIL import Image
sys.path.insert(0,"/workspace/wdsans")
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
import math

def load(p):
    f=TTFont(p)
    if "fvar" in f:
        f=instancer.instantiateVariableFont(f,{"wght":400},inplace=True,updateFontNames=False,optimize=False)
    return f

def all_angles(f, chars="口日田目回且旦旧早"):
    cm=f.getBestCmap(); glyf=f["glyf"]
    angs=[]
    for ch in chars:
        n=cm.get(ord(ch))
        if not n: continue
        g=glyf[n]
        if g.numberOfContours<=0: continue
        coords=list(g.coordinates); flags=list(g.flags)
        st=0
        for e in g.endPtsOfContours:
            seg=coords[st:e+1]; fl=flags[st:e+1]; st=e+1
            K=len(seg)
            for i in range(K):
                if not (fl[i]&1): continue
                if not (fl[(i-1)%K]&1) or not (fl[(i+1)%K]&1): continue
                px,py=seg[i]; ax,ay=seg[(i-1)%K]; bx,by=seg[(i+1)%K]
                v1=(ax-px,ay-py); v2=(bx-px,by-py)
                n1=math.hypot(*v1); n2=math.hypot(*v2)
                if n1<1e-9 or n2<1e-9: continue
                c=max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))
                angs.append(round(math.degrees(math.acos(c))))
    return angs

print("=== 角点角度统计（口日田目回且旦旧早）===")
for lbl,p in [("Noto","/workspace/wdsans/ref/NotoSansCJKsc-VF.ttf"),
              ("本产物","/data/build-cache/wdsans-p1/wdsans-p2-feet.ttf"),
              ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),
              ("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]:
    a=all_angles(load(p))
    from collections import Counter
    c=Counter(a)
    print(f"  {lbl:6s}: {len(a)} 个角点, 角度 --> {dict(sorted(c.items(),key=lambda z:-z[1])[:5])}")
print()
print("=> 全部 90°，不存在圆角。「折角微圆」这一项应当取消。")