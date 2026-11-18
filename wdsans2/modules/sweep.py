#!/usr/bin/env python3
# sweep - 扫描 seg3终点(x,y) 与 bar右端 的组合, 找撇厚≈28 的配置
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

T = "/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf"
OUT = "/workspace/wdsans2/build/sweep"
os.makedirs(OUT, exist_ok=True)
SZ = 2000; UPEM = 1000

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

def thick(path):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), "多", fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    a = a[r[0]:r[-1]+1, c[0]:c[-1]+1]
    T2 = ndimage.distance_transform_edt(a)*2
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
        vals.append(T2[y,x0:x1+1].max()*k)
    return sum(vals)/len(vals) if vals else 0

f0 = TTFont(T, lazy=True); gs0=f0.getGlyphSet(); cm0=f0.getBestCmap()
gn = cm0[ord("多")]
rp = RecordingPen(); gs0[gn].draw(rp); f0.close()
C = contours_from_pen(rp.value)
bar_i = body_i = None
for ci,c in enumerate(C):
    b=bb(c); sig="".join(s[0] for s in c["segs"])
    if b[3]<600: continue
    if sig=="LLL": bar_i=ci
    elif sig=="LCCCL": body_i=ci
bar_bb = bb(C[bar_i]); bar_right = bar_bb[1]; bar_bot = bar_bb[2]; bar_top = bar_bb[3]
s3 = C[body_i]["segs"][3]
apex = np.array(s3[-1], float)
print("T6: bar_right=%.0f bar y[%.0f,%.0f]  apex=(%.0f,%.0f)" % (bar_right, bar_bot, bar_top, apex[0], apex[1]))
print()
print("扫描: 目标撇厚 ≈ 28-32")

results = []
for xoff in [0, 8, 15, 23]:
    for ysel, yname in [(710,"bar_bot+2"),(718,"mid"),(725,"apex_y")]:
        f = TTFont(T); g=f.getGlyphSet(); cmm=f.getBestCmap()
        NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
        nbd = NEW[body_i]
        tx = bar_right + xoff
        nbd["segs"][3] = ["C", s3[1], s3[2], (tx, ysel)]
        del nbd["segs"][4:]
        cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
        old = csT[gn]
        csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
        f["post"].formatType = 3.0; f["post"].glyphOrder = None
        p = os.path.join(OUT, "x%d_%s.otf" % (xoff, yname))
        f.save(p); f.close()
        th = thick(p)
        results.append((abs(th-30), xoff, yname, tx, ysel, th))
        print("  xoff=%2d %-10s -> end=(%.0f,%.0f)  撇厚=%.0f" % (xoff, yname, tx, ysel, th))

results.sort()
print()
print("最接近 30 的配置: xoff=%d %s 撇厚=%.0f" % (results[0][1], results[0][2], results[0][5]))