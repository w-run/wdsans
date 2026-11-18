#!/usr/bin/env python3
# tradeoff - 横笔拉长量 vs 撇厚, 找平衡点 (250档)
#
# 从 T6 出度, 把 bar 右端和目标点 end_x 按比例 t 插值:
#   t=0   -> T6 原样 (bar 745, end 768)   撇薄但横笔有缺口
#   t=1   -> R34 状态 (bar 770, end 770)  撇粗但无缺口
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

SRC="/workspace/wdsans2/build/masters_T6/master-ExtraLight-250.otf"
OUT="/workspace/wdsans2/build/tradeoff"
os.makedirs(OUT, exist_ok=True)

f0=TTFont(SRC, lazy=True); gs0=f0.getGlyphSet(); cm0=f0.getBestCmap()
rp=RecordingPen(); gs0[cm0[ord("多")]].draw(rp); f0.close()
C0=contours_from_pen(rp.value)
bar_i=body_i=None
for ci,c in enumerate(C0):
    sig="".join(s[0] for s in c["segs"]); P=allpts(c)
    if sig=="LLL" and P[:,1].max()>600: bar_i=ci
    elif sig=="LCCCL" and P[:,1].max()>600: body_i=ci
bar_p=allpts(C0[bar_i]); body_p=allpts(C0[body_i])
bar_x0=bar_p[:,0].max()   # T6 bar 右端
seg3=C0[body_i]["segs"][3]; apex=np.array(seg3[-1],float)
fold=np.array(C0[body_i]["segs"][4][-1],float)
target=770.0
print("T6: bar_right=%.0f apex_x=%.0f fold_x=%.0f target=%.0f" % (bar_x0, apex[0], fold[0], target))
print()
print("%-6s %-12s %-12s %-8s" % ("t","bar_right","seg3_end_x","撇厚"))
for i in range(6):
    t = i/5.0
    new_bar = bar_x0 + (target-bar_x0)*t
    new_apex = apex[0] + (target-apex[0])*t
    f = TTFont(SRC)
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C0]
    nb = NEW[bar_i]; nb["start"] = (new_bar, nb["start"][1])
    s2 = nb["segs"][2]; nb["segs"][2] = ["L", (new_bar, s2[-1][1])]
    nbd = NEW[body_i]; s3 = nbd["segs"][3]
    nbd["segs"][3] = ["C", s3[1], s3[2], (new_apex, apex[1])]
    del nbd["segs"][4:]
    cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    gn=cm0[ord("多")]; old=csT[gn]
    csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    p=os.path.join(OUT,"t%d.otf"%i)
    f.save(p); f.close()
    print("%-6.1f %-12.0f %-12.0f %-8.0f" % (t, new_bar, new_apex, thick(p)))
print()
print("SHS 参照: 撇厚 %.0f" % thick("/workspace/wdsans/ref/shs/shs-250.otf"))