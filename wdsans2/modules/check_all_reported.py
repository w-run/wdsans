#!/usr/bin/env python3
"""check_all_reported - 检查用户报告的全部字是否被 m_ledge 改动"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R28 = '/workspace/wdsans2/build/masters_R28/master-Regular-400.otf'

CH = "极条目角眼得散形几界日田由甲申曲电青表素责毒"


def bars(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    out = []
    for i, c in enumerate(C):
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
        out.append((round(P[:,0].min()), round(P[:,0].max()), round(P[:,1].min()), round(P[:,1].max())))
    return out


print('%-3s %s' % ('字', '被 m_ledge 拉伸的轮廓'))
n = 0
for ch in CH:
    a = bars(R15, ch); b = bars(R28, ch)
    if not a or not b or len(a) != len(b):
        continue
    ch_list = []
    for i, (x0, x1, y0, y1) in enumerate(a):
        X0, X1, Y0, Y1 = b[i]
        if abs(X1 - x1) > 5:
            ch_list.append("c%d x1 %d->%d (+%d)" % (i, x1, X1, X1-x1))
    if ch_list:
        n += 1
        print("%-3s %s" % (ch, " | ".join(ch_list)))
print()
print('共 %d/%d 字被改动' % (n, len(CH)))