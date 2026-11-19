#!/usr/bin/env python3
"""单字变体实验: 大 的捺末端多种改法，直接目视挑选"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
CH = "大"

def seg_starts(c):
    segs = c["segs"]
    st = [c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": st.append(s[1])
        elif s[0]=="C": st.append(s[3])
        elif s[0]=="Q": st.append(s[2])
        elif s[0]=="QM": st.append(s[1][-1])
    return st

def slen(segs, st, j):
    s = segs[j]
    if s[0]=="L": e=s[1]
    elif s[0]=="C": e=s[3]
    elif s[0]=="Q": e=s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e,dtype=float)-np.array(st[j],dtype=float)))

def find_endfaces(C):
    """返回 [(ci, j)] 端面段位置"""
    out = []
    for ci, c in enumerate(C):
        segs = c["segs"]; N = len(segs)
        if N < 3: continue
        st = seg_starts(c)
        for j, s in enumerate(segs):
            if s[0] != "C": continue
            L = slen(segs, st, j)
            if L < 30 or L > 130: continue
            if slen(segs, st, (j-1)%N) < 150: continue
            if slen(segs, st, (j+1)%N) < 150: continue
            out.append((ci, j))
    return out

def make_variant(tag, mode, param=0.0):
    f = TTFont(SRC)
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    csT = f["CFF2"].cff.topDictIndex[0].CharStrings
    gn = cm[ord(CH)]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    hits = find_endfaces(C)
    for ci, j in hits:
        c = C[ci]; s = c["segs"][j]
        p0 = np.array(seg_starts(c)[j], dtype=float)
        c1 = np.array(s[1], dtype=float)
        c2 = np.array(s[2], dtype=float)
        end = np.array(s[3], dtype=float)
        if mode == "L":
            c["segs"][j] = ["L", tuple(end)]
        elif mode == "Lshrink":
            # 沿 p0->end 方向把 end 往回收 param 单位
            v = end - p0
            L = np.linalg.norm(v)
            if L > param + 10:
                newend = p0 + v/L*(L-param)
                c["segs"][j] = ["L", tuple(newend)]
        elif mode == "Lperpend":
            # end 沿法向朝内收 param
            v = end - p0
            L = np.linalg.norm(v)
            if L > 1e-6:
                nrm = np.array([-v[1], v[0]])/L
                # 判断朝内方向: 与 c1 同侧
                if (c1-p0).dot(nrm) < 0: nrm = -nrm
                newend = end - nrm*param
                c["segs"][j] = ["L", tuple(newend)]
    old = csT[gn]
    csT[gn] = make_charstring(C, old.private, old.globalSubrs)
    f["post"].formatType = 3.0
    f["post"].glyphOrder = None
    out = "/workspace/wdsans2/build/tv_%s.otf" % tag
    f.save(out); f.close()
    print("  %-12s -> %s  (改 %d 段)" % (tag, out, len(hits)))
    return out

print("生成变体:")
make_variant("orig", "none")
make_variant("L", "L")
make_variant("Ls20", "Lshrink", 20)
make_variant("Ls40", "Lshrink", 40)
make_variant("Lp15", "Lperpend", 15)
make_variant("Lp30", "Lperpend", 30)
