#!/usr/bin/env python3
# v2test - m_barple2 在 多 上的三档试验
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple2
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

B = "/workspace/wdsans2/build/masters_T6/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUT = "/workspace/wdsans2/build/v2"
os.makedirs(OUT, exist_ok=True)
SZ = 2000; UPEM = 1000

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

print("%-8s %-10s %s" % ("weight","撇厚","细节"))
for tag in ["250","400","900"]:
    f = TTFont(B + FN[tag]); gs=f.getGlyphSet(); cm=f.getBestCmap()
    gn = cm[ord("多")]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = m_barple2.find(C)
    if not hits:
        print("  %s 无命中" % tag); f.close(); continue
    for h in hits:
        print("  %s hit: bar_right=%.0f bar_bot=%.0f bar_h=%.0f -> dx=%.0f dy=%.0f" % (
            tag, h[2], h[3], h[4], 0.28*h[4], 0.07*h[4]))
    NEW = m_barple2.apply(C, hits)
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, "V_%s.otf" % tag)
    f.save(p); f.close()
    print("      撇厚=%.0f" % thick(p))

print()
print("基准: SHS-250=28 SHS-400=?. SHS-900=?")
for w in [250,400,900]:
    print("  SHS-%d 撇厚=%.0f" % (w, thick("/workspace/wdsans/ref/shs/shs-%d.otf"%w)))