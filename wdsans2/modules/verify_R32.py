#!/usr/bin/env python3
# verify_R32 - 确认 326 字的 dy 已归零, 且未触及未列入的字
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

D = "/workspace/wdsans2/build/masters_R32/"
FN = {"250":"master-ExtraLight-250.otf","400":"master-Regular-400.otf","900":"master-Heavy-900.otf"}

def bb(c):
    pts=[np.array(c["start"],float)]
    for s in c["segs"]:
        if s[0]=="QM":
            for q in s[1]: pts.append(np.array(q,float))
        elif s[0]=="C": pts.extend([np.array(s[1],float),np.array(s[2],float),np.array(s[3],float)])
        elif s[0]=="Q": pts.extend([np.array(s[1],float),np.array(s[2],float)])
        else: pts.append(np.array(s[1],float))
    P=np.array(pts); return P[:,0].min(),P[:,0].max(),P[:,1].min(),P[:,1].max()

idx = json.load(open(D + "index.json"))
print("验证 %d 字的 dy (应为 0):" % len(idx))
for tag in ["250","400","900"]:
    f = TTFont(D + FN[tag], lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    bad = 0; ok = 0
    for ks, (bi, ci) in idx.items():
        cp = int(ks)
        if cp not in cm: continue
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        if bi >= len(C) or ci >= len(C): continue
        bot = bb(C[bi])[2]
        end = np.array(C[ci]["segs"][-1][-1], float)
        if abs(end[1] - bot) < 1: ok += 1
        else: bad += 1
    f.close()
    print("  %s: OK=%d  bad=%d" % (tag, ok, bad))