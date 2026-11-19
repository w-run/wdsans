#!/usr/bin/env python3
"""方案 B: 不改段类型，只把端面段的 c2 控制点沿切线内收，让曲线末端趋直"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring
import numpy as np

SRC = "/workspace/wdsans2/build/masters_R37/master-Regular-400.otf"
TARGETS = "大人天夫文父"
PULL = 0.55   # c2 向 c1-end 连线靠拢的比例

def seg_starts(c):
    segs = c["segs"]
    starts = [c["start"]]
    for s in segs[:-1]:
        if s[0]=="L": starts.append(s[1])
        elif s[0]=="C": starts.append(s[3])
        elif s[0]=="Q": starts.append(s[2])
        elif s[0]=="QM": starts.append(s[1][-1])
    return starts

def seg_len(segs, starts, j):
    s = segs[j]
    if s[0]=="L": e=s[1]
    elif s[0]=="C": e=s[3]
    elif s[0]=="Q": e=s[2]
    else: return 0.0
    return float(np.linalg.norm(np.array(e,dtype=float)-np.array(starts[j],dtype=float)))

f = TTFont(SRC)
cm = f.getBestCmap(); gs = f.getGlyphSet()
csT = f["CFF2"].cff.topDictIndex[0].CharStrings

for pull in (0.4, 0.55, 0.7):
    f2 = TTFont(SRC)
    cs2 = f2["CFF2"].cff.topDictIndex[0].CharStrings
    gs2 = f2.getGlyphSet()
    n = 0
    for ch in TARGETS:
        cp = ord(ch)
        if cp not in cm: continue
        gn = cm[cp]
        rp = RecordingPen(); gs2[gn].draw(rp)
        C = contours_from_pen(rp.value)
        ch_n = 0
        for c in C:
            segs = c["segs"]; N = len(segs)
            if N < 3: continue
            st = seg_starts(c)
            for j, s in enumerate(segs):
                if s[0] != "C": continue
                L = seg_len(segs, st, j)
                if L < 30 or L > 130: continue
                Lp = seg_len(segs, st, (j-1)%N); Ln = seg_len(segs, st, (j+1)%N)
                if Lp < 150 or Ln < 150: continue
                # c2 向 (c1 + end)/2 方向内收
                c1 = np.array(s[1], dtype=float)
                c2 = np.array(s[2], dtype=float)
                end = np.array(s[3], dtype=float)
                target = (c1 + end) / 2.0
                new_c2 = c2 + (target - c2) * pull
                c["segs"][j] = ["C", tuple(s[1]), tuple(new_c2), tuple(s[3])]
                ch_n += 1
        if ch_n:
            old = cs2[gn]
            cs2[gn] = make_charstring(C, old.private, old.globalSubrs)
            n += 1
    f2["post"].formatType = 3.0
    f2["post"].glyphOrder = None
    out = "/workspace/wdsans2/build/test_c2_%d.otf" % int(pull*100)
    f2.save(out)
    f2.close()
    print("pull=%.2f -> %s (%d 字)" % (pull, out, n))
