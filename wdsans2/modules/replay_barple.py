#!/usr/bin/env python3
# replay_barple - 用当前 m_barple 在 T6 上重放, 测撇厚
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
sys.path.insert(0, '/workspace/wdsans2/modules')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import m_barple, m_by0align
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

SZ=2000; UPEM=1000
def thick(path, ch="多"):
    ft = ImageFont.truetype(path, SZ)
    img = Image.new("L", (SZ*2, SZ*2), 0)
    ImageDraw.Draw(img).text((SZ//4, SZ//4), ch, fill=255, font=ft)
    a = np.array(img) > 128
    r = np.where(a.any(axis=1))[0]; c = np.where(a.any(axis=0))[0]
    if not len(r): return 0
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

SW={250:30.0, 400:77.0, 900:150.0}
FN={250:"master-ExtraLight-250.otf",400:"master-Regular-400.otf",900:"master-Heavy-900.otf"}
OUT="/workspace/wdsans2/build/replay"; os.makedirs(OUT, exist_ok=True)

print("%-6s %-12s %-12s %-12s %s" % ("档","T6(原)","重放barple","SHS","MOD(历史)"))
for w in [250,400,900]:
    src="/workspace/wdsans2/build/masters_T6/"+FN[w]
    f=TTFont(src)
    gs=f.getGlyphSet(); cm=f.getBestCmap()
    gn=cm[ord("多")]
    rp=RecordingPen(); gs[gn].draw(rp)
    C=contours_from_pen(rp.value)
    hits=m_barple.find(C, SW[w])
    if not hits:
        print("%d: 无命中" % w); f.close(); continue
    NEW=m_barple.apply(C, hits)
    cff2=f["CFF2"].cff; td=cff2[cff2.fontNames[0]]; csT=td.CharStrings
    old=csT[gn]
    csT[gn]=make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType=3.0; f["post"].glyphOrder=None
    p=os.path.join(OUT,"P_%d.otf"%w)
    f.save(p); f.close()
    shs=thick("/workspace/wdsans/ref/shs/shs-%d.otf"%w)
    mod=thick("/workspace/wdsans2/build/masters_MOD/"+FN[w])
    print("%-6d %-12.0f %-12.0f %-12.0f %.0f" % (
        w, thick(src), thick(p), shs, mod))