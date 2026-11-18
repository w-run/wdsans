#!/usr/bin/env python3
# alt_path - 三条路线对比: R34现状 / seg3回到T6的725 / SHS
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

T6="/workspace/wdsans2/build/masters_T6/"; R34="/workspace/wdsans2/build/masters_R34/"
OUT="/workspace/wdsans2/build/altpath"; os.makedirs(OUT, exist_ok=True)
FN={250:"master-ExtraLight-250.otf",400:"master-Regular-400.otf",900:"master-Heavy-900.otf"}

for w in [250,400,900]:
    # T6 的溢出点 y
    f6=TTFont(T6+FN[w],lazy=True); gs6=f6.getGlyphSet(); cm6=f6.getBestCmap()
    rp6=RecordingPen(); gs6[cm6[ord("多")]].draw(rp6); f6.close()
    C6=contours_from_pen(rp6.value)
    apex_y=None
    for c in C6:
        sig="".join(s[0] for s in c["segs"]); P=allpts(c)
        if sig=="LCCCL" and P[:,1].max()>600:
            apex_y=float(c["segs"][3][-1][1]); break
    # R34 上应用
    f=TTFont(R34+FN[w]); gs=f.getGlyphSet(); cm=f.getBestCmap()
    gn=cm[ord("多")]
    rp=RecordingPen(); gs[gn].draw(rp)
    C=contours_from_pen(rp.value)
    NEW=[{"start":c["start"],"segs":[list(s) for s in c["segs"]]} for c in C]
    n=0
    for ci,c in enumerate(C):
        sig="".join(s[0] for s in c["segs"]); P=allpts(c)
        if sig=="LCCC" and P[:,1].max()>600 and P[:,0].max()>600:
            s3=NEW[ci]["segs"][2]; e=np.array(s3[-1],float)
            NEW[ci]["segs"][2]=["C", s3[1], s3[2], (e[0], apex_y)]
            n+=1
    if not n:
        print("%d: 未找到" % w); f.close(); continue
    cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    old=csT[gn]
    csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    p=os.path.join(OUT,"A_%d.otf"%w)
    f.save(p); f.close()
    print("%d: seg3终点 y -> %.0f | 撇厚 R34=%.0f 新=%.0f SHS=%.0f" % (
        w, apex_y, thick(R34+FN[w]), thick(p), thick("/workspace/wdsans/ref/shs/shs-%d.otf"%w)))