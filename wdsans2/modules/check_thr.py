#!/usr/bin/env python3
"""测试不同 dx/dy 阈值下 人 是否命中 + 总命中数 + 对照组"""
import sys
sys.path.insert(0,"/workspace/wdsans2/probe")
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

def hit_with(C, maxr):
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
            if abs(v[0])>abs(v[1])*maxr: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            out.append((ci,j))
    return out

CTRL="口回十中申甲田日国目一二三工王土士干平正生"
print("%-8s %10s %10s %10s %10s" % ("阈值","命中字","命中段","人命中","对照组"))
print("-"*54)
for r in (0.85, 0.90, 0.95, 1.00, 1.10):
    n=0; seg=0; ren=None
    for cp in cm:
        if not (0x4E00<=cp<=0x9FFF): continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        h=hit_with(C,r)
        if h:
            n+=1; seg+=len(h)
            if cp==0x4EBA: ren=len(h)
    # 对照组
    ch_=0
    for ch in CTRL:
        cp=ord(ch)
        if cp not in cm: continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        if hit_with(C,r): ch_+=1
    print("%-8.2f %10d %10d %10s %10d" % (r, n, seg, ren if ren else "-", ch_))
f.close()
