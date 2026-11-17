#!/usr/bin/env python3
"""final29 - R29 最终验证：ledge 误伤必须为 0"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
VF = '/workspace/static/wdsans/WDesignSans-VF.otf'


def boxes(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    out = {}
    for cp in [c for c in cm if 0x4E00 <= c <= 0x9FFF]:
        rp = RecordingPen()
        try:
            gs[cm[cp]].draw(rp)
        except Exception:
            continue
        C = contours_from_pen(rp.value)
        xs = []
        for c in C:
            xs.append(c["start"][0])
            for s in c["segs"]:
                if s[0] == "QM":
                    for p in s[1]: xs.append(p[0])
                elif s[0] in ("C","Q"):
                    for p in s[1:]: xs.append(p[0])
                else:
                    xs.append(s[1][0])
        out[cp] = (min(xs), max(xs))
    f.close()
    return out


print('读取 R15 基准...', flush=True)
A = boxes(R15)
print('读取 VF...', flush=True)
B = boxes(VF)

big = []
for cp in A:
    if cp not in B:
        continue
    d = max(abs(A[cp][0]-B[cp][0]), abs(A[cp][1]-B[cp][1]))
    if d > 100:
        big.append((d, chr(cp)))
big.sort(reverse=True)
print()
print('横向位移 >100 的字: %d 个' % len(big))
if big:
    print('  ' + ' '.join('%s%d' % (c,d) for d,c in big[:25]))
else:
    print('  (无) OK')

print()
print('=== 用户报告的 11 个字 ===')
for ch in "极条目角眼得散形几界混":
    cp = ord(ch)
    if cp in A and cp in B:
        d0 = abs(A[cp][0]-B[cp][0]); d1 = abs(A[cp][1]-B[cp][1])
        st = "OK" if max(d0,d1) < 5 else "CHANGED %d" % max(d0,d1)
        print("  %s  %s" % (ch, st))
print()
print('=== 出（应已修正）===')
if ord("出") in A and ord("出") in B:
    print("  出  R15 x[%.0f,%.0f] -> VF x[%.0f,%.0f]" % (A[ord("出")][0], A[ord("出")][1], B[ord("出")][0], B[ord("出")][1]))