#!/usr/bin/env python3
"""verify_r29 - 验证 R29 干净版"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R29 = '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'


def bars(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
    for c in C:
        P = [np.array(c["start"], float)]
        for s in c["segs"]:
            if s[0] == "QM":
                for p in s[1]: P.append(np.array(p, float))
            elif s[0] == "C":
                P.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
            elif s[0] == "Q":
                P.extend([np.array(s[1],float), np.array(s[2],float)])
            else:
                P.append(np.array(s[1], float))
        P = np.array(P)
        out.append((round(P[:,0].min()), round(P[:,0].max())))
    return out


print('%-4s %-30s %s' % ('字','R15->R29 轮廓x变化','判定'))
bad = 0
for ch in "极条目角眼得散形几界混到理腮膨璥出":
    a = bars(R15, ch); b = bars(R29, ch)
    if not a or not b:
        continue
    diffs = []
    for i, (x0, x1) in enumerate(a):
        if i >= len(b):
            break
        X0, X1 = b[i]
        if abs(X1-x1) > 5 or abs(X0-x0) > 5:
            diffs.append("c%d x[%d,%d]->[%d,%d]" % (i, x0, x1, X0, X1))
    status = "改动 " + " | ".join(diffs) if diffs else "未变 OK"
    if ch in "出":
        status = "(应改) " + (" | ".join(diffs) if diffs else "无变化!")
    print("%-4s %-30s %s" % (ch, "", status))