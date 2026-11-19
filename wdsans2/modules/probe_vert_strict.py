#!/usr/bin/env python3
"""加 dx 约束: 端面必须"接近垂直"(|dx| <= dy*0.9)"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

MASTER="/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
f=TTFont(MASTER,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()

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

def find(C, max_dx_ratio):
    hits=[]
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
            if L<40 or L>160: continue
            if v[1]<=0: continue
            if abs(v[0]) < 20: continue   # 已经足够垂直，不用改
            if abs(v[0]) > abs(v[1])*max_dx_ratio: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            hits.append((ci,j,round(L,0),round(float(v[0]),0),round(float(v[1]),0)))
    return hits

print("=== 不同 dx 约束下的命中数 ===")
print("%-8s %10s %10s %8s" % ("dx/dy上限","命中字","命中段","占比"))
print("-"*40)
for r in (0.95, 0.90, 0.85, 0.80, 0.75, 0.70):
    n=0; seg=0
    for cp in cm:
        if not (0x4E00<=cp<=0x9FFF): continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        h=find(C,r)
        if h: n+=1; seg+=len(h)
    print("%-8.2f %10d %10d %7.1f%%" % (r, n, seg, 100.0*n/20992))

print()
print("=== dx>=20 且 dx/dy<=0.85 的样例 ===")
n=0; samples=[]
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    h=find(C,0.85)
    if h:
        n+=1
        if len(samples)<20: samples.append((chr(cp),h))
print("命中 %d 字" % n)
for ch,h in samples:
    print("  %s: %s" % (ch,h))

print()
print("=== 对照组（dx/dy<=0.35）===")
CTRL="口回十中申甲田日国目一二三工王土士干平正生"
c_hit=[]
for ch in CTRL:
    cp=ord(ch)
    if cp not in cm: continue
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    h=find(C,0.85)
    if h: c_hit.append((ch,h))
print("对照组 %d 字，%d 命中 %s" % (len(CTRL), len(c_hit), "OK" if not c_hit else c_hit))
f.close()
