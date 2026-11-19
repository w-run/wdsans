#!/usr/bin/env python3
"""分析: 带 blend 的字能否安全改（保留 blend，只改默认值）

结论先行: 
- 大/天/夫/文 等已改字的 blend=0（单档固定值），make_charstring 重建安全
- 人/丞/今 等 blend>0，make_charstring 重建会丢插值数据 -> 保存失败
- 正确做法: 只改 program 里默认值，保留 deltas
"""
import sys
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF="/workspace/static/wdsans/WDesignSans-VF.otf"
f=TTFont(VF,lazy=True)
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
cm=f.getBestCmap(); gs=f.getGlyphSet()

# 统计: 待改的 1040 字里有多少含 blend
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
import numpy as np
from canonpen3 import contours_from_pen

need=[]; need_blend=[]; need_noblend=[]
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    hit=False
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
        if max(p[0] for p in pts)<700: continue
        for j,s in enumerate(segs):
            if s[0] not in ("C","Q"): continue
            e=np.array(s[-1],dtype=float); p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<40 or L>160 or v[1]<=0: continue
            if abs(v[0])<20: continue
            if abs(v[0])>abs(v[1])*MAXR: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            hit=True; break
        if hit: break
    if hit:
        need.append(cp)
        prog=csT[gn].program
        nb=prog.count("blend") if prog else 0
        if nb>0: need_blend.append((chr(cp),nb))
        else: need_noblend.append(chr(cp))

print("待改 %d 字" % len(need))
print("  其中含 blend: %d 字" % len(need_blend))
print("  不含 blend:   %d 字" % len(need_noblend))
print()
print("含 blend 样例: %s" % need_blend[:12])
print()
print("不含 blend 样例: %s" % need_noblend[:12])
f.close()
