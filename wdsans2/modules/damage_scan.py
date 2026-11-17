#!/usr/bin/env python3
"""damage_scan - 全库对比 R15(无ledge) vs R28，量化 m_ledge 真实破坏面"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R28 = '/workspace/wdsans2/build/masters_R28/master-Regular-400.otf'


def allpts(c):
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
    return np.array(P)


def boxes(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    cjk = [cp for cp in cm if 0x4E00 <= cp <= 0x9FFF]
    for cp in cjk:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        out[cp] = [tuple(round(v) for v in (allpts(c)[:,0].min(), allpts(c)[:,0].max(),
                                         allpts(c)[:,1].min(), allpts(c)[:,1].max())) for c in C]
    f.close()
    return out


print('读取 R15...', flush=True)
A = boxes(R15)
print('读取 R28...', flush=True)
B = boxes(R28)

big = []   # 位移 > 100
mid = []   # 位移 20~100
small = [] # 位移 5~20
for cp in A:
    if cp not in B or len(A[cp]) != len(B[cp]):
        continue
    mx = 0
    for (a, b) in zip(A[cp], B[cp]):
        mx = max(mx, abs(a[1] - b[1]), abs(a[0] - b[0]))
    if mx > 100:
        big.append((mx, chr(cp)))
    elif mx > 20:
        mid.append((mx, chr(cp)))
    elif mx > 5:
        small.append((mx, chr(cp)))

print()
print('位移 >100: %d 字' % len(big))
big.sort(reverse=True)
print('  ' + ' '.join('%s%d' % (c, d) for d, c in big[:40]))
print('位移 20~100: %d 字' % len(mid))
mid.sort(reverse=True)
print('  ' + ' '.join('%s%d' % (c, d) for d, c in mid[:40]))
print('位移 5~20: %d 字' % len(small))
print()
print('合计被改: %d / %d' % (len(big)+len(mid)+len(small), len(A)))