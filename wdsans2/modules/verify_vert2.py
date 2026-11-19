#!/usr/bin/env python3
import sys, json, os, subprocess
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from canonpen3 import contours_from_pen
import numpy as np
from PIL import Image
from scipy.spatial import ConvexHull

SRC="/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
NEW="/workspace/wdsans2/build/tv2_all.otf"
MAP=json.load(open("/workspace/wdsans2/build/tv2_map.json"))

def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

def endface(path, key, is_glyph):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    gn = key if is_glyph else cm[ord(key)]
    rp=RecordingPen(); gs[gn].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    for c in C:
        segs=c["segs"]; N=len(segs)
        if N<3: continue
        st=seg_starts(c)
        pts=[tuple(c["start"])]
        for s in segs:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts.append(tuple(s[3]))
            elif s[0]=="Q": pts.append(tuple(s[2]))
            elif s[0]=="QM": pts.append(tuple(s[1][-1]))
        if max(p[0] for p in pts) < 700: continue
        for j,s in enumerate(segs):
            if s[0] not in ("C","Q","L"): continue
            e=np.array(s[-1],dtype=float); p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<40 or L>160 or v[1]<=0: continue
            return s[0], float(v[0]), float(v[1])
    return None

print("=== 端面段（右上轮廓的向上短段）===")
print("%-4s %-6s %6s %8s %8s %8s" % ("字","版本","类型","dx","dy","垂直"))
print("-"*44)
for ch,g in MAP.items():
    for lbl,path,key,isg in (("原版",SRC,ch,False),("改后",NEW,g,True),("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf",ch,False)):
        r=endface(path,key,isg)
        if r:
            print("%-4s %-6s %6s %8.0f %8.0f %8s" % (ch,lbl,r[0],r[1],r[2],"是" if abs(r[1])<1 else "否"))
    print()

# 像素凸包
PX=1200
def raster(path,key,isg):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    gn = key if isg else cm[ord(key)]
    p=SVGPathPen(gs); gs[gn].draw(p); d=p.getCommands(); f.close()
    svg=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-50 -1080 1100 1140" width="%d" height="%d">'
         '<g transform="scale(1,-1)"><path d="%s" fill="black"/></g></svg>')%(PX,PX,d)
    tag="%s_%s"%(os.path.basename(path).split(".")[0][:8],key)
    sp="/tmp/r_%s.svg"%tag; png="/tmp/r_%s.png"%tag
    open(sp,"w").write(svg)
    subprocess.run(["/usr/bin/rsvg-convert","-w",str(PX),"-h",str(PX),"-o",png,sp],check=False,capture_output=True)
    if not os.path.exists(png): return None
    a=np.array(Image.open(png).convert("L"))>128
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

print("=== 端面凸包比（1.00=平切）===")
print("%-4s %8s %8s %8s" % ("字","原版","改后","OPPO"))
print("-"*34)
A=[]
for ch,g in MAP.items():
    r0=raster(SRC,ch,False); c0=convex(r0) if r0 is not None else None
    r1=raster(NEW,g,True); c1=convex(r1) if r1 is not None else None
    r2=raster("/workspace/wdsans/ref/ops/ops-400.ttf",ch,False); c2=convex(r2) if r2 is not None else None
    print("%-4s %8s %8s %8s" % (ch,
        "%.3f"%c0 if c0 else "-","%.3f"%c1 if c1 else "-","%.3f"%c2 if c2 else "-"))
    if c0 and c1 and c2: A.append((c0,c1,c2))
if A:
    print("-"*34)
    print("%-4s %8.3f %8.3f %8.3f" % ("均值",
        np.mean([x[0] for x in A]),np.mean([x[1] for x in A]),np.mean([x[2] for x in A])))
