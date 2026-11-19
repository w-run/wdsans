#!/usr/bin/env python3
"""最终验证 VF_R41_final.otf"""
import sys, os
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import ConvexHull
import uharfbuzz as hb

OLD="/workspace/static/wdsans/WDesignSans-VF.otf"
NEW="/workspace/wdsans2/build/VF_R41_final.otf"

def render(path,ch,px=1200):
    ft=ImageFont.truetype(path,px); W=px*2
    img=Image.new("L",(W,W),0)
    ImageDraw.Draw(img).text((px//2,px//4),ch,fill=255,font=ft)
    a=np.array(img)>128
    r=np.where(a.any(axis=1))[0]; c=np.where(a.any(axis=0))[0]
    if not len(r) or not len(c): return None
    return a[r[0]:r[-1]+1,c[0]:c[-1]+1]

def convex(m):
    h,w=m.shape
    sub=m[int(h*0.55):,int(w*0.50):]
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

CH=["大","天","夫","文","父","之","久","义","个","人"]
print("=== 凸包比 ===")
print("%-4s %10s %10s %10s" % ("字","旧","新","OPPO"))
print("-"*38)
A=[]
for ch in CH:
    c0=convex(render(OLD,ch)); c1=convex(render(NEW,ch))
    c2=convex(render("/workspace/wdsans/ref/ops/ops-400.ttf",ch))
    print("%-4s %10s %10s %10s" % (ch,
        "%.3f"%c0 if c0 else "-","%.3f"%c1 if c1 else "-","%.3f"%c2 if c2 else "-"))
    if c0 and c1 and c2: A.append((c0,c1,c2))
if A:
    print("-"*38)
    print("%-4s %10.3f %10.3f %10.3f" % ("均值",
        np.mean([x[0] for x in A]),np.mean([x[1] for x in A]),np.mean([x[2] for x in A])))

print()
print("=== 曲线占比（m_termface 教训门禁）===")
for lbl,p in (("旧",OLD),("新",NEW),("SHS","/workspace/wdsans/ref/shs/shs-400.otf")):
    f=TTFont(p,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    tot=0; cur=0
    for cp in cm:
        if not (0x4E00<=cp<=0x9FFF): continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        for c in C:
            for s in c["segs"]:
                tot+=1
                if s[0] in ("C","Q","QM"): cur+=1
    f.close()
    print("  %-4s 曲线占比 %.2f%%" % (lbl, 100.0*cur/max(1,tot)))

print()
print("=== HarfBuzz 排版回归 ===")
fa=hb.Font(hb.Face(hb.Blob.from_file_path(OLD)))
fb=hb.Font(hb.Face(hb.Blob.from_file_path(NEW)))
def shape(font,text,feats=None):
    buf=hb.Buffer(); buf.add_str(text); buf.guess_segment_properties()
    if feats: hb.shape(font,buf,feats)
    else: hb.shape(font,buf)
    return ([i.codepoint for i in buf.glyph_infos],
            [(p.x_advance,p.x_offset,p.y_offset) for p in buf.glyph_positions])
CASES=[("永国字体",None),("设置·消息",None),("0123456789",None),("Hamburgefonstiv",None),
       ("123",{"sups":True}),("1/2",{"frac":True}),("、。",{"chws":True}),
       ("b\u0301",None),("12:34",None),("a:b",None)]
d=0
for t,f in CASES:
    if shape(fa,t,f)!=shape(fb,t,f):
        d+=1; print("  !! %r %s" % (t,f))
print("  %d 用例，%d 不同 %s" % (len(CASES),d,"OK" if d==0 else "!!"))

print()
print("=== 元数据 ===")
a=TTFont(OLD,lazy=True); b=TTFont(NEW,lazy=True)
print("  表 %d->%d  glyphs %d->%d  cmap %d->%d" % (
    len(set(a.keys())),len(set(b.keys())),
    a["maxp"].numGlyphs,b["maxp"].numGlyphs,
    len(a.getBestCmap()),len(b.getBestCmap())))
ga=sorted(set(fr.FeatureTag for fr in a["GPOS"].table.FeatureList.FeatureRecord))
gb=sorted(set(fr.FeatureTag for fr in b["GPOS"].table.FeatureList.FeatureRecord))
print("  GPOS %d->%d chws=%s vchw=%s" % (len(ga),len(gb),"chws" in gb,"vchw" in gb))
oa=a["OS/2"]; ob=b["OS/2"]
print("  OS2 v%d->v%d typo=%.2fem bit7=%s" % (oa.version,ob.version,
    (ob.sTypoAscender-ob.sTypoDescender)/1000.0,"ON" if ob.fsSelection&0x80 else "off"))
a.close(); b.close()
