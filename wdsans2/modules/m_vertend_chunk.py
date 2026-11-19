#!/usr/bin/env python3
"""分块累积: 每 150 字保存一次，重新加载继续（避免内存峰值）"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np, gc

SRC="/workspace/static/wdsans/WDesignSans-VF.otf"
WORK="/workspace/wdsans2/build/work_vf.otf"
MAXR=0.90
CHUNK=150

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

# 1) 收集
f=TTFont(SRC,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
todo=[]
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    h=detect(C)
    if h: todo.append((cp,gn,len(h)))
f.close()
print("待改 %d 字" % len(todo))

# 2) 分块处理
import shutil
shutil.copy(SRC, WORK)
total=0
for i in range(0, len(todo), CHUNK):
    chunk = todo[i:i+CHUNK]
    f=TTFont(WORK)
    gs2=f.getGlyphSet()
    csT=f["CFF2"].cff.topDictIndex[0].CharStrings
    n=0
    for cp,gn,nh in chunk:
        rp=RecordingPen()
        try: gs2[gn].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        hits=detect(C)
        if not hits: continue
        ok=True
        for ci,j in hits:
            if ci>=len(C) or j>=len(C[ci]["segs"]): ok=False; break
            if C[ci]["segs"][j][0] not in ("C","Q"): ok=False; break
        if not ok: continue
        for ci,j in hits:
            segs=C[ci]["segs"]; st=seg_starts(C[ci])
            p0=np.array(st[j],dtype=float); e=np.array(segs[j][-1],dtype=float)
            C[ci]["segs"][j]=["L",(float(p0[0]),float(e[1]))]
        old=csT[gn]
        csT[gn]=make_charstring(C, old.private, old.globalSubrs)
        n+=1
    f["post"].formatType=3.0
    f["post"].glyphOrder=None
    f.save(WORK)
    f.close(); gc.collect()
    total+=n
    print("  块 %d-%d: 改 %d 字  累计 %d" % (i, i+len(chunk), n, total), flush=True)

os.replace(WORK, "/workspace/wdsans2/build/VF_R42.otf")
print("完成 总改 %d 字" % total)
