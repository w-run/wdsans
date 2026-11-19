#!/usr/bin/env python3
"""精确实现: 解析 program 的 op 结构, 找到端面段, 把 dx 默认值设 0"""
import sys
sys.path.insert(0,"/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

VF="/workspace/static/wdsans/WDesignSans-VF.otf"
f=TTFont(VF,lazy=True)
csT=f["CFF2"].cff.topDictIndex[0].CharStrings
cm=f.getBestCmap(); gs=f.getGlyphSet()

OPS={'rmoveto':2,'rlineto':2,'rrcurveto':6,'hlineto':1,'vlineto':1,
     'hhcurveto':4,'vvcurveto':4,'hvcurveto':4,'vhcurveto':4}

def analyze(prog):
    """返回 [(op, [(default, delta_list), ...], op_idx)]
    每个坐标解码为 (default, deltas)"""
    out=[]
    i=0; n=len(prog)
    while i<n:
        v=prog[i]
        if isinstance(v,str):
            if v=='blend':
                i+=1; continue
            op=v
            nargs=OPS.get(op,0)
            if nargs:
                out.append((op,nargs,i))
            i+=1; continue
        i+=1
    return out

# 手工解析 人: 找 idx 145 那个 rrcurveto (18 regions)
gn=cm[0x4EBA]
rp=RecordingPen(); gs[gn].draw(rp)
prog=csT[gn].program
print("=== 人 idx 89-147 结构 ===")
# idx 89 rlineto (dx=-71,dy=-70) 撇
# idx 145 blend -> 146 rrcurveto (18 regions)
# 从 idx 90 开始到 144 是 18*? 个数字
print("idx 90..144 数字个数:", 144-90+1)
print("若 18 regions 且 6 参数: 需要 6*(1+18)=114 个数字")
print("实际 idx 90..143 = %d 个, idx 144=18(regions), idx 145=blend" % (143-90+1))
print()
print("第一个坐标(dx1) = idx 90 起 19 个: 默认=%s deltas=%s" % (prog[90], prog[91:109]))
print("第二个坐标(dy1) = idx 109 起 19 个: 默认=%s deltas=%s" % (prog[109], prog[110:128]))
f.close()
