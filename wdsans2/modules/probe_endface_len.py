#!/usr/bin/env python3
"""对比端面段长度: 我们 vs OPPO"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

FONTS = [("我们","/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"),
         ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf"),
         ("HOS","/workspace/wdsans/ref/hos/hos-400.ttf")]
CHARS = ["大","人","天","夫","文","父"]

def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

def analyze(path, ch):
    f=TTFont(path,lazy=True); cm=f.getBestCmap(); gs=f.getGlyphSet()
    if ord(ch) not in cm: f.close(); return None
    rp=RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C=contours_from_pen(rp.value)
    out=[]
    for c in C:
        segs=c["segs"]; N=len(segs)
        if N<3: continue
        st=seg_starts(c)
        # 找 bbox 右下区域
        pts=[tuple(c["start"])]
        for s in segs:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts.append(tuple(s[3]))
            elif s[0]=="Q": pts.append(tuple(s[2]))
            elif s[0]=="QM": pts.append(tuple(s[1][-1]))
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        if max(xs) < 700: continue
        # 逐段: 找方向向上的短段（端面）
        for j,s in enumerate(segs):
            t=s[0]
            if t=="L": e=np.array(s[1],dtype=float)
            elif t=="C": e=np.array(s[3],dtype=float)
            elif t=="Q": e=np.array(s[2],dtype=float)
            else: continue
            p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<20 or L>200: continue
            # 端面特征: 方向偏上 (dy>0) 且短
            if v[1] <= 0: continue
            # 前后段长度
            def sl(k):
                ss=segs[k]
                if ss[0]=="L": ee=ss[1]
                elif ss[0]=="C": ee=ss[3]
                elif ss[0]=="Q": ee=ss[2]
                else: return 0.0
                return float(np.linalg.norm(np.array(ee,dtype=float)-np.array(st[k],dtype=float)))
            if sl((j-1)%N) < 100 or sl((j+1)%N) < 100: continue
            out.append(dict(j=j, kind=t, L=L, dx=float(v[0]), dy=float(v[1]),
                            end=(float(e[0]),float(e[1]))))
    return out

print("=== 端面段（短、方向向上、前后长段）===")
print("%-4s %-6s %4s %4s %8s %8s %8s" % ("字","字体","段","类型","长度","dx","dy"))
print("-"*56)
for ch in CHARS:
    for lbl,p in FONTS:
        r = analyze(p,ch)
        if not r: continue
        for it in r:
            print("%-4s %-6s %4d %4s %8.1f %8.1f %8.1f" % (
                ch,lbl,it["j"],it["kind"],it["L"],it["dx"],it["dy"]))
    print()
