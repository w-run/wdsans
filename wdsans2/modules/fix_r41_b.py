#!/usr/bin/env python3
"""直接在部署版 VF 上应用垂直端面改动（保留全部表与特性）"""
import sys, os, json
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

CUR="/workspace/static/wdsans/WDesignSans-VF.otf"
OUT="/workspace/wdsans2/build/VF_R41_final.otf"
IDX=json.load(open("/workspace/wdsans2/build/vertend_idx.json"))

def seg_starts(c):
    segs=c["segs"]; st=[c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

f=TTFont(CUR)
gs=f.getGlyphSet()
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
n_g=0; n_s=0; skip=0
for gn,hits in IDX.items():
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception:
        skip+=1; continue
    C=contours_from_pen(rp.value)
    ok=True
    for ci,j in hits:
        if ci>=len(C) or j>=len(C[ci]["segs"]):
            ok=False; break
        if C[ci]["segs"][j][0] not in ("C","Q"):
            ok=False; break
    if not ok:
        skip+=1; continue
    for ci,j in hits:
        segs=C[ci]["segs"]
        st=seg_starts(C[ci])
        p0=np.array(st[j],dtype=float)
        e=np.array(segs[j][-1],dtype=float)
        C[ci]["segs"][j]=["L",(float(p0[0]),float(e[1]))]
        n_s+=1
    old=csT[gn]
    csT[gn]=make_charstring(C, old.private, old.globalSubrs)
    n_g+=1

print("改 %d 字 / %d 段  跳过 %d" % (n_g,n_s,skip))
f["post"].formatType=3.0
f["post"].glyphOrder=None
f.save(OUT)
f.close()
print("已保存 %s (%.1fMB)" % (OUT, os.path.getsize(OUT)/1e6))
