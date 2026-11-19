#!/usr/bin/env python3
"""精确分析 大 的捺末端几何，找出正确改法"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OURS="/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
OPPO="/workspace/wdsans/ref/ops/ops-400.ttf"

def edges(path, ch, name):
    f=TTFont(path,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    print("=== %s %s ===" % (name,ch))
    for c in C:
        pts=[tuple(c["start"])]
        for s in c["segs"]:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts+=[tuple(s[1]),tuple(s[2]),tuple(s[3])]
            elif s[0]=="Q": pts+=[tuple(s[1]),tuple(s[2])]
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        w=max(xs)-min(xs); h=max(ys)-min(ys)
        if w<200 or h<200: continue
        # 只看含捺末端的轮廓（x 大 y 小）
        if max(xs) < 800 or min(ys) > -40: continue
        print("  轮廓 bbox x[%.0f,%.0f] y[%.0f,%.0f]" % (min(xs),max(xs),min(ys),max(ys)))
        for j,s in enumerate(c["segs"]):
            t=s[0]
            if t=="L": print("    [%d] L   -> (%.0f,%.0f)" % (j,s[1][0],s[1][1]))
            elif t=="C": print("    [%d] C   c1(%.0f,%.0f) c2(%.0f,%.0f) -> (%.0f,%.0f)" % (j,s[1][0],s[1][1],s[2][0],s[2][1],s[3][0],s[3][1]))
    print()

edges(OURS,"大","我们")
edges(OPPO,"大","OPPO")

# 像素级: 量末端厚度
print("=== 末端厚度对比（沿笔画法向）===")
def tip_thickness(path,ch,px=1200):
    ft=ImageFont.truetype(path,px); W=px*2
    img=Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((px//2,px//4),ch,fill=255,font=ft)
    a=np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    m=a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    h,w=m.shape
    sub=m[int(h*0.60):, int(w*0.55):]
    pts=np.argwhere(sub)
    if len(pts)<200: return None
    cc=pts.mean(axis=0); d=pts-cc
    cov=d.T.dot(d)/len(pts); ev,evec=np.linalg.eigh(cov)
    main=evec[:,np.argmax(ev)]
    if main[0]<0: main=-main
    t=d.dot(main); n=np.array([-main[1],main[0]]); dn=d.dot(n)
    tmax=float(t.max()); span=float(t.max()-t.min())
    # 端面最后 10% 的宽度
    sel=t>=tmax-span*0.10
    if sel.sum()<20: return None
    w_end=float(dn[sel].max()-dn[sel].min())
    # 中段宽度
    selm=(t>=tmax-span*0.55)&(t<=tmax-span*0.35)
    w_mid=float(dn[selm].max()-dn[selm].min()) if selm.sum()>20 else 0
    return w_end, w_mid

for lbl,p in (("我们-改前",OURS),("OPPO",OPPO),("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")):
    r=tip_thickness(p,"大")
    if r:
        print("  %-10s 末端宽=%.0f 中段宽=%.0f 末端/中段=%.2f" % (lbl,r[0],r[1],r[0]/r[1] if r[1]>0 else 0))
