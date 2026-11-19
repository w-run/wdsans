#!/usr/bin/env python3
"""m_vertend_vf - 在 VF 上做垂直端面修改，保留 blend 插值数据

关键: 不能重建 charstring（会丢 blend），必须直接改 program 里的默认值。

blend 编码: 对每个坐标, [default, delta_1..delta_k, k, 'blend']
  改 dx 为 0 => 只把该坐标的 default 设 0, deltas 保留（插值仍然工作）
"""
import sys, os
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

VF=os.environ.get("WDS_VF","/workspace/static/wdsans/WDesignSans-VF.otf")
OUT=os.environ.get("WDS_OUT","/workspace/wdsans2/build/VF_R42.otf")
MAXR=0.90

OPS={'rmoveto':2,'rlineto':2,'rrcurveto':6,'hlineto':1,'vlineto':1,
     'hhcurveto':4,'vvcurveto':4,'hvcurveto':4,'vhcurveto':4}

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

def find_endfaces(C):
    """返回 [(轮廓序号, 段序号)]"""
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
        if max(p[0] for p in pts)<700: continue
        for j,s in enumerate(segs):
            if s[0] not in ("C","Q"): continue
            e=np.array(s[-1],dtype=float); p0=np.array(st[j],dtype=float)
            v=e-p0; L=float(np.linalg.norm(v))
            if L<40 or L>160 or v[1]<=0: continue
            if abs(v[0])<20: continue
            if abs(v[0])>abs(v[1])*MAXR: continue
            if slen(segs,st,(j-1)%N)<100 or slen(segs,st,(j+1)%N)<100: continue
            out.append((ci,j))
    return out

def parse_ops(prog):
    """解析 program 为 [(op, coord_start_idx, nargs, regions)]"""
    out=[]
    i=0; n=len(prog); coord_start=None; regions=0
    while i<n:
        v=prog[i]
        if isinstance(v,str):
            if v=='blend':
                i+=1; continue
            op=v
            nargs=OPS.get(op,0)
            if nargs:
                total=nargs*(1+regions) if regions>0 else nargs
                start=i-1-total+1 if regions>0 else i-nargs
                # 找 regions: 在 start-1 位置
                if regions>0:
                    start = i-1-total
                else:
                    start = i-nargs
                out.append((op,start,nargs,regions))
            regions=0
            i+=1; continue
        # 后面可能是 regions 数
        if i+1<n and prog[i+1]=='blend':
            regions=v
        i+=1
    return out

# 主流程
f=TTFont(VF)
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
cm=f.getBestCmap(); gs=f.getGlyphSet()

n_g=0; n_s=0; n_blend=0
for cp in cm:
    if not (0x4E00<=cp<=0x9FFF): continue
    gn=cm[cp]
    rp=RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C=contours_from_pen(rp.value)
    hits=find_endfaces(C)
    if not hits: continue
    n_g+=1; n_s+=len(hits)

print("检测: %d 字 / %d 段" % (n_g,n_s))
print("（本轮只做检测，修改逻辑需进一步验证 blend 定位）")
f.close()
