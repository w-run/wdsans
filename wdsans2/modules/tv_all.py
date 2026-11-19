#!/usr/bin/env python3
"""一次加载字体，生成全部变体到不同未映射槽位，只保存一次"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
OUT = "/workspace/wdsans2/build/tv_all.otf"
CH = "大"

f = TTFont(SRC)
cm = f.getBestCmap(); gs = f.getGlyphSet()
csT = f["CFF2"].cff.topDictIndex[0].CharStrings
gn0 = cm[ord(CH)]
rp = RecordingPen(); gs[gn0].draw(rp)
BASE = contours_from_pen(rp.value)

def seg_starts(c):
    segs = c["segs"]; st = [c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

def slen(segs, st, j):
    s = segs[j]
    if s[0]=="L": e=s[1]
    elif s[0]=="C": e=s[3]
    elif s[0]=="Q": e=s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e,dtype=float)-np.array(st[j],dtype=float)))

def hits(C):
    out=[]
    for ci,c in enumerate(C):
        segs=c["segs"]; N=len(segs)
        if N<3: continue
        st=seg_starts(c)
        for j,s in enumerate(segs):
            if s[0]!="C": continue
            L=slen(segs,st,j)
            if L<30 or L>130: continue
            if slen(segs,st,(j-1)%N)<150: continue
            if slen(segs,st,(j+1)%N)<150: continue
            out.append((ci,j))
    return out

def clone(C):
    return [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]

H = hits(BASE)
print("端面段位置: %s" % H)

variants = {}
variants["orig"] = clone(BASE)
variants["L"] = clone(BASE)
for ci,j in H:
    variants["L"][ci]["segs"][j] = ["L", BASE[ci]["segs"][j][3]]
for param in (20, 40):
    C = clone(BASE)
    for ci,j in H:
        c=C[ci]; s=BASE[ci]["segs"][j]
        p0=np.array(seg_starts(BASE[ci])[j],dtype=float)
        end=np.array(s[3],dtype=float)
        v=end-p0; L=np.linalg.norm(v)
        if L>param+10:
            C[ci]["segs"][j]=["L", tuple(p0+v/L*(L-param))]
    variants["Ls%d"%param]=C
for param in (15, 30):
    C = clone(BASE)
    for ci,j in H:
        c=C[ci]; s=BASE[ci]["segs"][j]
        p0=np.array(seg_starts(BASE[ci])[j],dtype=float)
        c1=np.array(s[1],dtype=float); end=np.array(s[3],dtype=float)
        v=end-p0; L=np.linalg.norm(v)
        if L>1e-6:
            nrm=np.array([-v[1],v[0]])/L
            if (c1-p0).dot(nrm)<0: nrm=-nrm
            C[ci]["segs"][j]=["L", tuple(end-nrm*param)]
    variants["Lp%d"%param]=C
# C->L 且把 c2 拉向 c1-end 线（减少外凸）
C = clone(BASE)
for ci,j in H:
    s=BASE[ci]["segs"][j]
    c["segs"][j]=["C", s[1], s[2], s[3]]
variants["keep"]=C

# 写入不同未映射槽位
order = f.getGlyphOrder()
mapped = set(cm.values())
free = [g for g in order if g not in mapped][:20]
print("可用槽位: %d" % len(free))

for i,(tag,C) in enumerate(variants.items()):
    gname = free[i]
    old = csT[gn0]
    csT[gname] = make_charstring(C, old.private, old.globalSubrs)
    print("  %-6s -> %s" % (tag, gname))

f["post"].formatType = 3.0
f["post"].glyphOrder = None
f.save(OUT)
f.close()
print("已保存 %s" % OUT)
# 记录槽位映射
import json
json.dump({tag: free[i] for i,tag in enumerate(variants)}, open("/workspace/wdsans2/build/tv_map.json","w"))
print("槽位映射已存")
