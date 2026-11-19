#!/usr/bin/env python3
"""m_vertend2 - 垂直端面 v2（阈值 0.90，覆盖「人」等 dx/dy 0.86 的字）

v1 用 0.85 -> 漏掉 人（dx/dy=0.859 差 0.6）
v2 用 0.90 -> 命中 8579 字，对照组仍 0 误伤
"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

CUR=os.environ.get("WDS_VF","/workspace/static/wdsans/WDesignSans-VF.otf")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/VF_R42.otf")
MAXR=0.90

def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st
def slen(segs,st,j):
    s=segs[j]
    if s[0]=="L": e=s[1]
    elif s[0]=="C": e=s[3]
    elif s[0]=="Q": e=s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e,dtype=float)-np.array(st[j],dtype=float)))

def detect(C):
    out=[]
    for ci,c in enumerate(C):
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
            if s[0] not in ("C","Q"): continue
            e=np.array(s[-1],dtype=float); p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<40 or L>160 or v[1]<=0: continue
            if abs(v[0])<20: continue
            if abs(v[0])>abs(v[1])*MAXR: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            out.append((ci,j))
    return out

print("m_vertend2: MAXR=%.2f  %s -> %s" % (MAXR, CUR, OUT))
f=TTFont(CUR)
cm=f.getBestCmap(); gs=f.getGlyphSet()
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
n_g=0; n_s=0; skip=0
ren_hit=False
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    hits=detect(C)
    if not hits: continue
    ok=True
    for ci,j in hits:
        if ci>=len(C) or j>=len(C[ci]["segs"]):
            ok=False; break
        if C[ci]["segs"][j][0] not in ("C","Q"):
            ok=False; break
    if not ok:
        skip+=1; continue
    for ci,j in hits:
        segs=C[ci]["segs"]
        st=seg_starts(C[ci])
        p0=np.array(st[j],dtype=float)
        e=np.array(segs[j][-1],dtype=float)
        C[ci]["segs"][j]=["L",(float(p0[0]),float(e[1]))]
        n_s+=1
    old=csT[gn]
    csT[gn]=make_charstring(C, old.private, old.globalSubrs)
    n_g+=1
    if cp==0x4EBA: ren_hit=True

print("  改 %d 字 / %d 段  跳过 %d" % (n_g,n_s,skip))
print("  人(U+4EBA) 命中: %s" % ren_hit)
if "--dry" in sys.argv:
    f.close()
    print("  (dry)")
    sys.exit(0)
f["post"].formatType=3.0
f["post"].glyphOrder=None
import gc
f.save(OUT)
f.close()
print("  已保存 %s (%.1fMB)" % (OUT, os.path.getsize(OUT)/1e6))
