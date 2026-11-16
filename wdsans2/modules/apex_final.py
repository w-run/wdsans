#!/usr/bin/env python3
"""apex_final - 最终验证"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
from fontTools.misc import bezierTools
import numpy as np

OLD = '/workspace/wdsans2/build/masters_R25/master-Regular-400.otf'
NEW = '/workspace/wdsans2/build/static_apex/master-Regular-400.otf'
HOS = '/workspace/wdsans/ref/hos/hos-400.ttf'
OPPO = '/workspace/wdsans/ref/ops4/OPPOSans4.ttf'


def flat(c, n=16):
    pts = [np.array(c['start'], float)]
    prev = pts[0]
    for s in c['segs']:
        if s[0] == 'L':
            p = np.array(s[1], float); pts.append(p); prev = p
        elif s[0] == 'C':
            P = [prev, np.array(s[1], float), np.array(s[2], float), np.array(s[3], float)]
            for i in range(1, n+1):
                pts.append(bezierTools.splitCubicAtT(*P, i/n)[0][-1])
            prev = P[3]
        elif s[0] == 'Q':
            P = [prev, np.array(s[1], float), np.array(s[2], float)]
            for i in range(1, n+1):
                pts.append(bezierTools.splitQuadraticAtT(*P, i/n)[0][-1])
            prev = P[2]
        elif s[0] == 'QM':
            for p in s[1]:
                pts.append(np.array(p, float))
            prev = pts[-1]
    return np.array(pts)


def topw(path, ch):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen()
    try: gs[cm[ord(ch)]].draw(rp)
    except Exception:
        f.close(); return None
    f.close()
    C = contours_from_pen(rp.value)
    if not C: return None
    P = np.vstack([flat(c) for c in C])
    gmax = P[:, 1].max()
    topx = P[P[:, 1] > gmax - 4][:, 0]
    w = topx.max() - topx.min() if len(topx) > 1 else 0
    return int(w), len(C)


print('=== 目标字 ===')
print('%-4s %-11s %-11s %-11s %-11s' % ('字','改前','改后','HOS','OPPO'))
for ch in '今合会含令全金余介企':
    r = [topw(p, ch) for p in (OLD, NEW, HOS, OPPO)]
    def f(t): return '%3d/%d' % t if t else '-'
    print('%-4s %-11s %-11s %-11s %-11s' % (ch, f(r[0]), f(r[1]), f(r[2]), f(r[3])))
print('')
print('=== 对照组 ===')
for ch in '口回十中申甲田日国目':
    a = topw(OLD, ch); b = topw(NEW, ch)
    flag = '  <<< 变了!' if a != b else '  ok'
    print('  %-4s %-10s %-10s%s' % (ch, str(a), str(b), flag))