#!/usr/bin/env python3
"""验证当前部署版的 R41 成果完整 + 统计还有多少字待修"""
import sys
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

VF="/workspace/static/wdsans/WDesignSans-VF.otf"
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

f=TTFont(VF,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
fixed=0; remain=0
remain_samples=[]
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    hit=False
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
            hit=True; break
        if hit: break
    if hit:
        remain+=1
        if len(remain_samples)<15: remain_samples.append(chr(cp))
f.close()
print("部署版 VF 中仍符合「待改」判据的字: %d" % remain)
print("样例: %s" % " ".join(remain_samples))
print()
print("说明: R41 已改 7646 字(0.85阈值)。这里用 0.90 阈值检测，")
print("      剩余的应为 0.85~0.90 之间被 v1 漏掉的字 + 已改过的不再匹配。")
