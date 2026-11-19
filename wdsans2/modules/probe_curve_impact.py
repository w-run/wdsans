#!/usr/bin/env python3
"""评估 C->L 对曲线占比的影响（m_termface 教训的门槛: 相对 SHS 偏差 <=2%）"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

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

def count_hits(C, maxr=0.85):
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
            if abs(v[0])<20: continue
            if abs(v[0])>abs(v[1])*maxr: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            hits.append((ci,j))
    return hits

# 统计三个字体: 我们的曲线占比 + 命中会裁掉多少曲线
for lbl, path in (("我们","/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"),
                  ("SHS","/workspace/wdsans/ref/shs/shs-400.otf")):
    f=TTFont(path,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    tot_seg=0; tot_curve=0; hit_seg=0
    for cp in cm:
        if not (0x4E00<=cp<=0x9FFF): continue
        rp=RecordingPen()
        try: gs[cm[cp]].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        for c in C:
            for s in c["segs"]:
                tot_seg+=1
                if s[0] in ("C","Q","QM"): tot_curve+=1
        if lbl=="我们":
            hit_seg += len(count_hits(C))
    f.close()
    pct = 100.0*tot_curve/max(1,tot_seg)
    new_pct = 100.0*(tot_curve-hit_seg)/max(1,tot_seg)
    print("%s: 总段=%d 曲线段=%d 曲线占比=%.2f%%" % (lbl, tot_seg, tot_curve, pct))
    if lbl=="我们":
        print("   命中段=%d  改后曲线占比=%.2f%%  (下降 %.2f 个百分点)" % (
            hit_seg, new_pct, pct-new_pct))
