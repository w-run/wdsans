#!/usr/bin/env python3
"""验证三档签名一致性（C->L 后必须 0 不一致）"""
import sys, os, json
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

SRC="/workspace/wdsans2/build/masters_R37"
NEW="/workspace/wdsans2/build/masters_R41"
MASTERS=[("master-ExtraLight-250.otf",250),("master-Regular-400.otf",400),("master-Heavy-900.otf",900)]
IDX=json.load(open("/workspace/wdsans2/build/vertend_idx.json"))

def sigs(path):
    f=TTFont(path,lazy=True); gs=f.getGlyphSet(); cm=f.getBestCmap()
    out={}
    for gn in IDX:
        rp=RecordingPen()
        try: gs[gn].draw(rp)
        except Exception: continue
        C=contours_from_pen(rp.value)
        out[gn]="/".join("".join(s[0] for s in c["segs"]) for c in C)
    f.close(); return out

print("=== 三档签名一致性（只检查改动的 %d 字）===" % len(IDX))
S=[]
for fn,w in MASTERS:
    p=os.path.join(NEW,fn)
    if not os.path.exists(p):
        print("  %d 缺失" % w); continue
    S.append((w,sigs(p)))
    print("  %d 档读取 %d 字" % (w,len(S[-1][1])))

if len(S)==3:
    a,b,c = S[0][1],S[1][1],S[2][1]
    diff_ab=sum(1 for k in a if a.get(k)!=b.get(k))
    diff_ac=sum(1 for k in a if a.get(k)!=c.get(k))
    print()
    print("  250 vs 400 不一致: %d" % diff_ab)
    print("  250 vs 900 不一致: %d" % diff_ac)
    if diff_ab or diff_ac:
        print("  !! VF 构建会失败")
        n=0
        for k in a:
            if a.get(k)!=b.get(k):
                print("    %s  250=%s  400=%s" % (k,a.get(k)[:30],str(b.get(k))[:30]))
                n+=1
                if n>=5: break
    else:
        print("  三档完全一致 OK")

# 顺便验证一个样例字的端面
print()
print("=== 样例: 大 的端面（400 档）===")
f=TTFont(os.path.join(NEW,"master-Regular-400.otf"),lazy=True)
gs=f.getGlyphSet(); cm=f.getBestCmap()
rp=RecordingPen(); gs[cm[ord("大")]].draw(rp); f.close()
C=contours_from_pen(rp.value)
for ci,c in enumerate(C):
    segs=c["segs"]
    st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    pts=[tuple(c["start"])]
    for s in segs:
        if s[0]=="L": pts.append(tuple(s[1]))
        elif s[0]=="C": pts.append(tuple(s[3]))
        elif s[0]=="Q": pts.append(tuple(s[2]))
        elif s[0]=="QM": pts.append(tuple(s[1][-1]))
    if max(p[0] for p in pts) < 700: continue
    sig="".join(s[0] for s in segs)
    print("  轮廓%d %s" % (ci,sig))
    for j,s in enumerate(segs):
        e=s[-1]; p0=st[j]
        import numpy as np
        v=np.array(e,dtype=float)-np.array(p0,dtype=float)
        print("    [%d] %s (%.0f,%.0f)->(%.0f,%.0f) dx=%.0f dy=%.0f" % (
            j,s[0],p0[0],p0[1],e[0],e[1],v[0],v[1]))
