#!/usr/bin/env python3
"""受控实验: 只改 4 个测试字的端面 C->L，看凸包比是否改善"""
import sys, os
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
OUT = "/workspace/wdsans2/build/test_endface.otf"
TARGETS = "大人天夫文父"

def find_endfaces(c):
    """找端面段: 短C + 前后长段"""
    segs = c["segs"]; n = len(segs)
    if n < 3: return []
    starts = [c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": starts.append(s[1])
        elif s[0]=="C": starts.append(s[3])
        elif s[0]=="Q": starts.append(s[2])
        elif s[0]=="QM": starts.append(s[1][-1])
    def slen(j):
        s = segs[j]
        if s[0]=="L": e=s[1]
        elif s[0]=="C": e=s[3]
        elif s[0]=="Q": e=s[2]
        else: return 0.0
        return float(np.linalg.norm(np.array(e,dtype=float)-np.array(starts[j],dtype=float)))
    res = []
    for j, s in enumerate(segs):
        if s[0] != "C": continue
        L = slen(j)
        if L < 30 or L > 130: continue
        Lp = slen((j-1) % n); Ln = slen((j+1) % n)
        if Lp < 150 or Ln < 150: continue
        res.append(j)
    return res

f = TTFont(SRC)
cm = f.getBestCmap(); gs = f.getGlyphSet()
csT = f["CFF2"].cff.topDictIndex[0].CharStrings

n_fixed = 0
for ch in TARGETS:
    cp = ord(ch)
    if cp not in cm: continue
    gn = cm[cp]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    changed = 0
    for c in C:
        for j in find_endfaces(c):
            s = c["segs"][j]
            end = s[3]
            c1 = s[1]
            # C->L: 保留端点，把控制点信息抹掉（直线到端点）
            # 但为了保持"平切"，需要保证直线方向合理 —— 直接用 c1 -> end 的切线
            c["segs"][j] = ["L", end]
            changed += 1
    if changed:
        old = csT[gn]
        csT[gn] = make_charstring(C, old.private, old.globalSubrs)
        n_fixed += 1
        print("  %s: 改 %d 段" % (ch, changed))

f["post"].formatType = 3.0
f["post"].glyphOrder = None
f.save(OUT)
f.close()
print("已保存 %s  改写 %d 字" % (OUT, n_fixed))
