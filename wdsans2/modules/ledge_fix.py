#!/usr/bin/env python3
"""ledge_fix - 修正 m_ledge：加居中判据，找出全部误报"""
import sys, os, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
R16 = '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'
TARGET = 90.0
MIN_RATIO = 2.8
MAX_H = 200.0
CENTER_TOL = 120.0


def endp(s):
    if s[0] == 'QM': return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def allpts(C):
    xs=[]; ys=[]
    for c in C:
        xs.append(c['start'][0]); ys.append(c['start'][1])
        for s in c['segs']:
            if s[0]=='QM':
                for p in s[1]: xs.append(p[0]); ys.append(p[1])
            elif s[0]=='C':
                xs.extend([s[1][0],s[2][0],s[3][0]]); ys.extend([s[1][1],s[2][1],s[3][1]])
            elif s[0]=='Q':
                xs.extend([s[1][0],s[2][0]]); ys.extend([s[1][1],s[2][1]])
            else:
                xs.append(s[1][0]); ys.append(s[1][1])
    return min(xs), max(xs), min(ys), max(ys)


def find_bar_OLD(C):
    """原判据：只要求 ymax 靠近字顶"""
    gx0, gx1, gy0, gy1 = allpts(C)
    best = None
    for ci, c in enumerate(C):
        segs = c['segs']
        if not all(s[0]=="L" for s in segs): continue
        if len(segs) not in (3,4): continue
        P = np.array([[c["start"][0],c["start"][1]]] + [[endp(s)[0],endp(s)[1]] for s in segs], float)
        x0,x1 = P[:,0].min(), P[:,0].max(); y0,y1 = P[:,1].min(), P[:,1].max()
        w = x1-x0; h = max(y1-y0,1)
        if w < 300: continue
        if w/h < MIN_RATIO: continue
        if h > MAX_H: continue
        if y1 < gy1 - 150: continue
        if best is None or y1 > best[0]:
            best = (y1, ci, P, w, h, gx1, x0, x1)
    return best


def find_bar_NEW(C):
    """新判据：加居中 + 放宽 ymax 窗口"""
    gx0, gx1, gy0, gy1 = allpts(C)
    gcen = (gx0 + gx1) / 2
    best = None
    for ci, c in enumerate(C):
        segs = c['segs']
        if not all(s[0]=="L" for s in segs): continue
        if len(segs) not in (3,4): continue
        P = np.array([[c["start"][0],c["start"][1]]] + [[endp(s)[0],endp(s)[1]] for s in segs], float)
        x0,x1 = P[:,0].min(), P[:,0].max(); y0,y1 = P[:,1].min(), P[:,1].max()
        w = x1-x0; h = max(y1-y0,1)
        if w < 300: continue
        if w/h < MIN_RATIO: continue
        if h > MAX_H: continue
        if y1 < gy1 - 320: continue
        cen = (x0 + x1) / 2
        if abs(cen - gcen) > CENTER_TOL: continue   # 居中判据
        if best is None or y1 > best[0]:
            best = (y1, ci, P, w, h, gx1, x0, x1)
    return best


f = TTFont(R15, lazy=True)
gs = f.getGlyphSet(); cm = f.getBestCmap()
cjk = [(cp, gn) for cp, gn in cm.items() if 0x4E00 <= cp <= 0x9FFF]
print('检查 %d 字' % len(cjk), flush=True)

only_old = []   # 旧判据会改、新判据不改 -> 误报
both = []      # 两者都会改
only_new = []  # 只有新判据会改

for cp, gn in cjk:
    rp = RecordingPen()
    try: gs[gn].draw(rp)
    except Exception: continue
    C = contours_from_pen(rp.value)
    o = find_bar_OLD(C); n = find_bar_NEW(C)
    o_need = o and (o[5] - o[7] > TARGET + 0.5)
    n_need = n and (n[5] - n[7] > TARGET + 0.5)
    if o_need and not n_need: only_old.append(chr(cp))
    elif o_need and n_need: both.append(chr(cp))
    elif n_need and not o_need: only_new.append(chr(cp))
f.close()

print()
print('旧判据会改、新判据跳过（= 误报，共 %d 字）:' % len(only_old))
print('  ' + ' '.join(only_old[:60]))
print()
print('两者都改（%d 字）:' % len(both))
print('  ' + ' '.join(both[:40]))
print()
print('只有新判据改（%d 字）:' % len(only_new))
print('  ' + ' '.join(only_new[:40]))

json.dump({'only_old': only_old, 'both': both, 'only_new': only_new},
          open('/workspace/wdsans2/build/ledge_fix.json','w'), ensure_ascii=False)