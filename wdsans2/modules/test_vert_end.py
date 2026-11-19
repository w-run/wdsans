#!/usr/bin/env python3
"""方案 C: 端面段改成"垂直 L"（dx=0），长度匹配参考"""
import sys, os, json
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
OUT = "/workspace/wdsans2/build/tv2_all.otf"
CHARS = ["大","人","天","夫","文","父"]

f = TTFont(SRC)
cm = f.getBestCmap(); gs = f.getGlyphSet()
csT = f["CFF2"].cff.topDictIndex[0].CharStrings
order = f.getGlyphOrder()
mapped = set(cm.values())
free = [g for g in order if g not in mapped and g != ".notdef"][:30]

def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

def slen(segs, st, j):
    s=segs[j]
    if s[0]=="L": e=s[1]
    elif s[0]=="C": e=s[3]
    elif s[0]=="Q": e=s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e,dtype=float)-np.array(st[j],dtype=float)))

def find_endface(C):
    """找端面段: 短 + dy>0 + 前后长段"""
    out=[]
    for ci,c in enumerate(C):
        segs=c["segs"]; N=len(segs)
        if N<3: continue
        st=seg_starts(c)
        # 只要 x>700 的轮廓（右侧）
        pts=[tuple(c["start"])]
        for s in segs:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts.append(tuple(s[3]))
            elif s[0]=="Q": pts.append(tuple(s[2]))
            elif s[0]=="QM": pts.append(tuple(s[1][-1]))
        if max(p[0] for p in pts) < 700: continue
        for j,s in enumerate(segs):
            if s[0] not in ("C","Q"): continue
            e=np.array(s[-1],dtype=float)
            p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<40 or L>160: continue
            if v[1] <= 0: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            out.append((ci,j))
    return out

count = 0
for idx, ch in enumerate(CHARS):
    cp=ord(ch)
    if cp not in cm: continue
    gn=cm[cp]
    rp=RecordingPen(); gs[gn].draw(rp)
    C=contours_from_pen(rp.value)
    hits=find_endface(C)
    if not hits:
        print("  %s: 未命中" % ch); continue
    for ci,j in hits:
        s=C[ci]["segs"][j]
        p0=np.array(seg_starts(C[ci])[j],dtype=float)
        e=np.array(s[-1],dtype=float)
        # 改成垂直 L: 保持终点 y，x 对齐起点 x（即端面垂直）
        new_end = (float(p0[0]), float(e[1]))
        C[ci]["segs"][j] = ["L", new_end]
        count += 1
        print("  %s: 段[%d,%d] %s -> 垂直L 从(%.0f,%.0f)到(%.0f,%.0f)" % (ch, ci, j, s[0], p0[0], p0[1], new_end[0], new_end[1]))
    old=csT[gn]
    csT[gn]=make_charstring(C, old.private, old.globalSubrs)

f["post"].formatType=3.0
f["post"].glyphOrder=None
# 把这 6 个字复制到未映射槽位以便渲染对比（因为 atlas 只用原槽位）
for idx, ch in enumerate(CHARS):
    cp=ord(ch)
    if cp not in cm: continue
    gname = free[idx]
    old = csT[cm[cp]]
    # 复制 charstring
    csT[gname] = old
    print("  %s -> 槽位 %s" % (ch, gname))

f.save(OUT); f.close()
json.dump({ch: free[i] for i,ch in enumerate(CHARS)}, open("/workspace/wdsans2/build/tv2_map.json","w"))
print("已保存 %s  改 %d 段" % (OUT, count))
