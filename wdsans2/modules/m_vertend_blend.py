#!/usr/bin/env python3
"""m_vertend_blend - 保留 blend 的垂直端面修改

关键思路:
  1. 用 getNumRegions() 取得该 charstring 的 regions 数
  2. 按 blend 编码格式精确解析 program
  3. 找到端面段的 dx，把它的「默认值」改成 0（deltas 保留）
  4. 用 setProgram() 写回（不重建 charstring，blend 结构不变）
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
     'hhcurveto':4,'vvcurveto':4,'hvcurveto':4,'vhcurveto':4,
     'rcurveline':None,'rlinecurve':None}

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

def parse_program(prog, nregions):
    """返回 [(op, [coord_default_idx...], op_idx, nargs)]
    coord_default_idx 是每个参数的默认值在 prog 中的索引"""
    out=[]
    i=0; n=len(prog); stack=[]
    while i<n:
        v=prog[i]
        if isinstance(v,str):
            if v=='blend':
                i+=1; continue
            op=v
            nargs=OPS.get(op)
            if nargs:
                # stack 里最后 nargs 项是默认值
                if len(stack)>=nargs:
                    stack=stack[-nargs:]
                    out.append((op,[s[1] for s in stack],[s[0] for s in stack],i))
                stack=[]
            i+=1; continue
        # 数字
        if i+2<n and prog[i+1]=='blend':
            # 这是 regions 数
            i+=1; continue
        stack.append((v,i))
        i+=1
    return out

print("m_vertend_blend: %s -> %s" % (VF,OUT))
f=TTFont(VF)
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
cm=f.getBestCmap(); gs=f.getGlyphSet()

# 先验证 人 的解析
gn=cm[0x4EBA]
cs=csT[gn]
rp=RecordingPen(); gs[gn].draw(rp)
nr = cs.getNumRegions() if hasattr(cs,'getNumRegions') else 0
print("  人 getNumRegions() = %s" % nr)
print("  program 长度 = %d" % len(cs.program))
segs=parse_program(cs.program, nr)
print("  解析段数 = %d" % len(segs))
for op,idxs,vals,oi in segs:
    print("    %-10s defaults=%s (idx %s, op_idx %d)" % (op,vals,idxs,oi))
f.close()
