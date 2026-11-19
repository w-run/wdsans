#!/usr/bin/env python3
import sys, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

MASTER="/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
VF="/workspace/static/wdsans/WDesignSans-VF.otf"

# 人 在 master 和 VF 里分别是什么
for lbl,p in (("master","/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"),
              ("VF",VF)):
    f=TTFont(p,lazy=True); cm=f.getBestCmap()
    print("%s: 人(U+4EBA) -> %s" % (lbl, cm.get(0x4EBA)))
    # 人 的康熙部首 U+2F08
    print("%s: ⼈(U+2F08) -> %s" % (lbl, cm.get(0x2F08)))
    f.close()

print()
# 检查 U+4EBA 在 VF 中是否被改
IDX=json.load(open("/workspace/wdsans2/build/vertend_idx.json"))
print("索引中 uni4EBA:", "uni4EBA" in IDX)
print("索引中 uni2F08:", "uni2F08" in IDX)
print()

# 看 master 的 人 是否被检测为命中
mf=TTFont(MASTER,lazy=True); mgs=mf.getGlyphSet(); mcm=mf.getBestCmap()
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

gn=mcm[0x4EBA]
rp=RecordingPen(); mgs[gn].draw(rp)
C=contours_from_pen(rp.value)
print("master 人 (%s) 轮廓:" % gn)
for ci,c in enumerate(C):
    segs=c["segs"]; N=len(segs); st=seg_starts(c)
    pts=[tuple(c["start"])]
    for s in segs:
        if s[0]=="L": pts.append(tuple(s[1]))
        elif s[0]=="C": pts.append(tuple(s[3]))
        elif s[0]=="Q": pts.append(tuple(s[2]))
        elif s[0]=="QM": pts.append(tuple(s[1][-1]))
    xmax=max(p[0] for p in pts)
    print("  轮廓%d %s xmax=%.0f" % (ci,"".join(x[0] for x in segs),xmax))
    for j,s in enumerate(segs):
        e=s[-1]; p0=st[j]
        v=np.array(e,dtype=float)-np.array(p0,dtype=float)
        L=float(np.linalg.norm(v))
        ok = (s[0] in ("C","Q") and 40<=L<=160 and v[1]>0
              and abs(v[0])>=20 and abs(v[0])<=abs(v[1])*0.85
              and slen(segs,st,(j-1)%N)>=100 and slen(segs,st,(j+1)%N)>=100)
        if s[0] in ("C","Q"):
            print("    [%d] %s L=%.0f dx=%.0f dy=%.0f  %s" % (
                j,s[0],L,v[0],v[1], "HIT" if ok else ""))
mf.close()
