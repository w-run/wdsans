#!/usr/bin/env python3
# c2_scale - 三档 c2dy 扫描, 求与横笔厚的比例关系
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ=2000; UPEM=1000
def thick(path, ch="多"):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
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

def allpts(c):
    P=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: P.append(np.array(q,float))
        elif s[0]=="C": P.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": P.extend([np.array(s[1],float),np.array(s[2],float)])
        else: P.append(np.array(s[1],float))
    return np.array(P)

OUT="/workspace/wdsans2/build/c2scale"; os.makedirs(OUT, exist_ok=True)
FN={250:"master-ExtraLight-250.otf",400:"master-Regular-400.otf",900:"master-Heavy-900.otf"}
SWR={250:29.0,400:67.0,900:127.0}   # 横笔厚度

for w in [250,400,900]:
    src="/workspace/wdsans2/build/masters_R34/"+FN[w]
    f0=TTFont(src, lazy=True); gs0=f0.getGlyphSet(); cm0=f0.getBestCmap()
    rp=RecordingPen(); gs0[cm0[ord("多")]].draw(rp); f0.close()
    C0=contours_from_pen(rp.value)
    body_i=None
    for ci,c in enumerate(C0):
        sig="".join(s[0] for s in c["segs"]); P=allpts(c)
        if sig=="LCCC" and P[:,1].max()>600 and P[:,0].max()>600: body_i=ci; break
    c=C0[body_i]; LAST=len(c["segs"])-1
    sL=c["segs"][LAST]
    base=thick(src); shs=thick("/workspace/wdsans/ref/shs/shs-%d.otf"%w)
    print("%d档: 原撇厚%.0f  SHS %.0f  横笔厚%.0f" % (w, base, shs, SWR[w]))
    best=None
    # 扫 0.0 ~ 1.2 倍横笔厚的 dy
    for ratio in [0.2,0.4,0.6,0.8,1.0,1.2]:
        dy = SWR[w]*ratio
        f = TTFont(src)
        NEW=[{"start":x["start"],"segs":[list(s) for s in x["segs"]]} for x in C0]
        NEW[body_i]["segs"][LAST] = ["C", sL[1], (sL[2][0], sL[2][1]+dy), sL[3]]
        cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
        gn=cm0[ord("多")]; old=csT[gn]
        csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
        f["post"].formatType=3.0; f["post"].glyphOrder=None
        p=os.path.join(OUT,"w%d_r%.1f.otf"%(w,ratio))
        f.save(p); f.close()
        th=thick(p)
        print("   ratio=%.1f dy=%.0f -> 撇厚%.0f" % (ratio, dy, th))
        if best is None or abs(th-shs)<abs(best[0]-shs): best=(th,ratio)
    print("   => best ratio=%.1f 撇厚=%.0f" % (best[1], best[0]))
    print()