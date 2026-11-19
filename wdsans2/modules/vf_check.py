#!/usr/bin/env python3
"""用 PIL 渲染（避免 SVG 问题）验证凸包比能否测量"""
import numpy as np, json
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

# 注: PIL 只能按 codepoint 渲染，无法按 glyph 名
# 所以换方案: 把改后的字写入临时字体的 cmap，用 PIL 渲染
import sys
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont

NEW="/workspace/wdsans2/build/tv2_all.otf"
MAP=json.load(open("/workspace/wdsans2/build/tv2_map.json"))
TMP="/workspace/wdsans2/build/tv2_mapped.otf"

f=TTFont(NEW)
for ch,g in MAP.items():
    for t in f["cmap"].tables:
        if t.isUnicode():
            t.cmap[ord(ch)] = g
f.save(TMP); f.close()
print("已写入 cmap: %s" % TMP)

def render(path, ch, px=1200):
    ft=ImageFont.truetype(path,px); W=px*2
    img=Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((px//2,px//4),ch,fill=255,font=ft)
    a=np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def convex(m):
    h,w=m.shape
    sub=m[int(h*0.55):, int(w*0.50):]
    pts=np.argwhere(sub)
    if len(pts)<300: return None
    cc=pts.mean(axis=0); d=pts-cc
    cov=d.T.dot(d)/len(pts); ev,evec=np.linalg.eigh(cov)
    main=evec[:,np.argmax(ev)]
    if main[0]<0: main=-main
    t=d.dot(main); tmax=float(t.max()); span=float(t.max()-t.min())
    sel=pts[t>=tmax-span*0.18]
    if len(sel)<50: return None
    try: return float(ConvexHull(sel).volume)/float(len(sel))
    except Exception: return None

print()
print("=== 端面凸包比（1.00=平切, >1.02=内凹）===")
print("%-4s %8s %8s %8s" % ("字","原版","改后","OPPO"))
print("-"*34)
A=[]
for ch in MAP:
    m0=render("/workspace/wdsans2/build/masters_R37/master-Regular-400.otf",ch)
    m1=render(TMP,ch)
    m2=render("/workspace/wdsans/ref/ops/ops-400.ttf",ch)
    c0=convex(m0) if m0 is not None else None
    c1=convex(m1) if m1 is not None else None
    c2=convex(m2) if m2 is not None else None
    print("%-4s %8s %8s %8s" % (ch,
        "%.3f"%c0 if c0 else "-", "%.3f"%c1 if c1 else "-", "%.3f"%c2 if c2 else "-"))
    if c0 and c1 and c2: A.append((c0,c1,c2))
if A:
    print("-"*34)
    print("%-4s %8.3f %8.3f %8.3f" % ("均值",
        np.mean([x[0] for x in A]), np.mean([x[1] for x in A]), np.mean([x[2] for x in A])))
