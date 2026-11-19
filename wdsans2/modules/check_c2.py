#!/usr/bin/env python3
import numpy as np, os
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull

VARIANTS = [("原版","/workspace/wdsans2/build/masters_R37/master-Regular-400.otf")]
for p in (40, 55, 70):
    path = "/workspace/wdsans2/build/test_c2_%d.otf" % p
    if os.path.exists(path):
        VARIANTS.append(("c2-%d%%" % p, path))
VARIANTS += [("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]
CHARS = ["大","人","天","夫","文","父"]
PX = 1200

def render(path, ch):
    ft = ImageFont.truetype(path, PX); W = PX*2
    img = Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((PX//2,PX//4),ch,fill=255,font=ft)
    a = np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1, c[0]:c[-1]+1]

def convexity(m):
    h,w = m.shape
    sub = m[int(h*0.55):, int(w*0.50):]
    pts = np.argwhere(sub)
    if len(pts)<300: return None
    cc=pts.mean(axis=0); d=pts-cc
    cov=d.T.dot(d)/len(pts); ev,evec=np.linalg.eigh(cov)
    main=evec[:,np.argmax(ev)]
    if main[0]<0: main=-main
    t=d.dot(main); tmax=float(t.max()); span=float(t.max()-t.min())
    sel=pts[t>=tmax-span*0.18]
    if len(sel)<50: return None
    try:
        return float(ConvexHull(sel).volume)/float(len(sel))
    except Exception:
        return None

def tipwidth(m):
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
    sel=t>=tmax-span*0.10
    if sel.sum()<20: return None
    we=float(dn[sel].max()-dn[sel].min())
    selm=(t>=tmax-span*0.55)&(t<=tmax-span*0.35)
    wm=float(dn[selm].max()-dn[selm].min()) if selm.sum()>20 else 0
    return we, wm

print("=== 凸包比 / 末端厚度比 ===")
print("%-8s %10s %12s" % ("方案","凸包比","末端/中段"))
print("-"*34)
AC={}; AT={}
for lbl,p in VARIANTS:
    cv=[]; tw=[]
    for ch in CHARS:
        m=render(p,ch)
        if m is None: continue
        r=convexity(m)
        if r: cv.append(r)
        t=tipwidth(m)
        if t and t[1]>0: tw.append(t[0]/t[1])
    if cv:
        print("%-8s %10.3f %12.2f" % (lbl, float(np.mean(cv)), float(np.mean(tw)) if tw else 0))
        AC[lbl]=cv; AT[lbl]=tw
