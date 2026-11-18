#!/usr/bin/env python3
# fix_by0 - 让 body 末点 y 跟随本档 bar_bot, 消除 250 冒出/900 台阶
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen, make_charstring

R = "/workspace/wdsans2/build/masters_R31/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}
OUT = "/workspace/wdsans2/build/fixby0"
os.makedirs(OUT, exist_ok=True)

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

CHAR = "多"
for tag in ["250","400","900"]:
    f = TTFont(R + FN[tag])
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    gn = cm[ord(CHAR)]
    rp = RecordingPen(); gs[gn].draw(rp)
    C = contours_from_pen(rp.value)
    NEW = [{"start": c["start"], "segs": [list(s) for s in c["segs"]]} for c in C]
    n_fixed = 0
    # 对每个 LLL 横笔 + 相邻 LCCC body，把 body 末点 y 对齐到 bar 下缘
    bars = [i for i,c in enumerate(C) if bb(c)[3] > 600 and "".join(s[0] for s in c["segs"]) == "LLL"]
    for bi in bars:
        bar_bot = bb(C[bi])[2]
        bar_right = bb(C[bi])[1]
        for ci, c in enumerate(C):
            if ci == bi: continue
            sig = "".join(s[0] for s in c["segs"])
            if sig not in ("LCCC","LCLC"): continue
            b = bb(c)
            if b[3] <= 600 or b[1] < 700: continue
            end = np.array(c["segs"][-1][-1], float)
            if abs(end[0] - bar_right) > 3: continue
            if abs(end[1] - bar_bot) < 1: continue
            NEW[ci]["segs"][-1] = list(NEW[ci]["segs"][-1])
            NEW[ci]["segs"][-1][-1] = (end[0], bar_bot)
            n_fixed += 1
            print("  %s: body c%d 末点 y %.0f -> %.0f (跟 bar c%d 下缘)" % (tag, ci, end[1], bar_bot, bi))
    if n_fixed == 0:
        print("  %s: 无改动" % tag); f.close(); continue
    cff2 = f["CFF2"].cff; td = cff2[cff2.fontNames[0]]; csT = td.CharStrings
    old = csT[gn]
    csT[gn] = make_charstring(NEW, old.private, old.globalSubrs)
    f["post"].formatType = 3.0; f["post"].glyphOrder = None
    p = os.path.join(OUT, "F_%s.otf" % tag)
    f.save(p); f.close()
    print("     saved " + p)