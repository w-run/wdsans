#!/usr/bin/env python3
"""统计垂直端面判据的全库命中 + 对照组检查"""
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

def find_vert_endface(C):
    """严格判据: xmax>700, 短段 40-160, dy>0, 前后>=100, 类型 C/Q"""
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
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            hits.append((ci,j,round(L,0),round(float(v[0]),0),round(float(v[1]),0)))
    return hits

n_glyph=0; n_hit=0; seg_total=0
samples=[]
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    n_glyph+=1
    h=find_vert_endface(C)
    if h:
        n_hit+=1; seg_total+=len(h)
        if len(samples)<15: samples.append((chr(cp),h))

print("CJK 字形: %d" % n_glyph)
print("命中字: %d (%.1f%%)" % (n_hit, 100.0*n_hit/max(1,n_glyph)))
print("命中段: %d" % seg_total)
print()
print("=== 样例 ===")
for ch,h in samples:
    print("  %s: %s" % (ch, h))
print()
# 对照组
print("=== 对照组（非撇捺字，应 0 命中）===")
CTRL="口回十中申甲田日国目一二三工王土士干平正生"
ctrl_hit=0
for ch in CTRL:
    cp=ord(ch)
    if cp not in cm: continue
    rp=RecordingPen()
    try: gs[cm[cp]].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    h=find_vert_endface(C)
    if h:
        ctrl_hit+=1
        print("  !! %s 命中: %s" % (ch,h))
print("  对照组 %d 字，%d 字命中 %s" % (len(CTRL), ctrl_hit, "OK" if ctrl_hit==0 else "!! 有误伤"))
f.close()
