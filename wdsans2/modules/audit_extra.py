#!/usr/bin/env python3
# audit_extra - 扩展审计: advance / 零长度段 / bbox 超界
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

VF = "/workspace/static/wdsans/WDesignSans-VF.otf"
f = TTFont(VF, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap(); hm = f["hmtx"]

def allpts(c):
    P = [np.array(c["start"], float)]
    for s in c["segs"]:
        if s[0] == "QM":
            for q in s[1]: P.append(np.array(q, float))
        elif s[0] == "C":
            P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
        elif s[0] == "Q":
            P.extend([np.array(s[1],float), np.array(s[2],float)])
        else:
            P.append(np.array(s[1], float))
    return np.array(P)

cps = [c for c in cm if 0x4E00 <= c <= 0x9FFF]
print("扫描 %d CJK..." % len(cps), flush=True)
bad_adv = []; zero_len = 0; over = []
for cp in cps:
    gn = cm[cp]
    if hm[gn][0] != 1000:
        bad_adv.append((chr(cp), hm[gn][0]))
    rp = RecordingPen()
    try:
        gs[gn].draw(rp)
    except Exception:
        continue
    C = contours_from_pen(rp.value)
    for c in C:
        P = allpts(c)
        prev = np.array(c["start"], float)
        for s in c["segs"]:
            e = np.array(s[-1], float)
            if float(np.hypot(*(e-prev))) < 0.5:
                zero_len += 1
            prev = e
        if P[:,0].min() < -200 or P[:,0].max() > 1200 or P[:,1].min() < -300 or P[:,1].max() > 1100:
            over.append((chr(cp), int(P[:,0].min()), int(P[:,0].max()), int(P[:,1].min()), int(P[:,1].max())))
f.close()
print()
print("1. advance != 1000 : %d 字" % len(bad_adv))
for t in bad_adv[:8]: print("     ", t)
print("2. 零长度段         : %d 处" % zero_len)
print("3. bbox 超界        : %d 字" % len(over))
for t in over[:8]: print("     ", t)