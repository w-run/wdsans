#!/usr/bin/env python3
# cp_sweep2 - 定位正确的 seg 索引后扫描
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ=2000; UPEM=1000
def thick(path):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "多", fill=255, font=ft)
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

SRC="/workspace/wdsans2/build/masters_R34/master-ExtraLight-250.otf"
OUT="/workspace/wdsans2/build/cpsweep2"; os.makedirs(OUT, exist_ok=True)
f0=TTFont(SRC, lazy=True); gs0=f0.getGlyphSet(); cm0=f0.getBestCmap()
rp=RecordingPen(); gs0[cm0[ord("多")]].draw(rp); f0.close()
C0=contours_from_pen(rp.value)
body_i=None
for ci,c in enumerate(C0):
    sig="".join(s[0] for s in c["segs"]); P=allpts(c)
    if sig=="LCCC" and P[:,1].max()>600 and P[:,0].max()>700: body_i=ci; break
c=C0[body_i]
print("body c%d segs=%d 起点(%.0f,%.0f)" % (body_i, len(c["segs"]), c["start"][0], c["start"][1]))
for k,s in enumerate(c["segs"]):
    e=s[-1]; ex=""
    if s[0]=="C": ex=" c1(%.0f,%.0f) c2(%.0f,%.0f)"%(s[1][0],s[1][1],s[2][0],s[2][1])
    print("  seg%d %s -> (%.0f,%.0f)%s"%(k,s[0],e[0],e[1],ex))
LAST=len(c["segs"])-1
sL=c["segs"][LAST]
print()
print("target seg = last seg%d" % LAST)
print("%-26s %-8s" % ("c2 (dy)","撇厚"))
best=None
for dy in [-20,-10,0,10,20,30]:
    c2x, c2y = sL[2][0], sL[2][1] + dy
    f = TTFont(SRC)
    NEW=[{"start":c["start"],"segs":[list(s) for s in c["segs"]]} for c in C0]
    NEW[body_i]["segs"][LAST] = ["C", sL[1], (c2x,c2y), sL[3]]
    cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    gn=cm0[ord("多")]; old=csT[gn]
    csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    p=os.path.join(OUT,"d%d.otf"%dy)
    f.save(p); f.close()
    th=thick(p)
    mark=" <<<" if abs(th-28)<4 else ""
    print("(%.0f,%.0f)          %.0f%s" % (c2x,c2y, th, mark))
    if best is None or abs(th-28)<abs(best[0]-28): best=(th,dy)
print()
print("最佳 c2dy=%d 撇厚=%.0f (SHS=%.0f)" % (best[1], best[0], thick("/workspace/wdsans/ref/shs/shs-250.otf")))