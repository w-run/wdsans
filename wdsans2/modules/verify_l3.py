#!/usr/bin/env python3
"""verify_l3 - 验证 m_ledge3 效果"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

R15 = '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'
OLD = '/workspace/wdsans2/build/masters_R16/master-Regular-400.otf'
NEW = '/workspace/wdsans2/build/masters_L3/master-Regular-400.otf'


def endp(s):
    if s[0]=='QM': return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def widest_bar(path, ch):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return None
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    gx1 = max(max([c["start"][0]] + [endp(s)[0] for s in c["segs"]]) for c in C)
    best = None
    for c in C:
        segs = c['segs']
        if not all(s[0]=="L" for s in segs): continue
        if len(segs) not in (3,4): continue
        xs = [c["start"][0]] + [endp(s)[0] for s in segs]
        ys = [c["start"][1]] + [endp(s)[1] for s in segs]
        x0,x1 = min(xs),max(xs); y0,y1 = min(ys),max(ys)
        w = x1-x0; h = max(y1-y0,1)
        if w < 300 or w/h < 2.8: continue
        if best is None or w > best[0]:
            best = (w, x0, x1, gx1)
    return best


print('%-4s %-24s %-24s %-24s' % ('字','R15(原始)','R16(旧m_ledge)','L3(新m_ledge)'))
for ch in "到理腮膨璥各冬条备务会俞拿":
    a = widest_bar(R15, ch); b = widest_bar(OLD, ch); c = widest_bar(NEW, ch)
    def fmt(x):
        return "x[%4.0f,%4.0f] 余%3.0f" % (x[1], x[2], x[3]-x[2]) if x else "-"
    print("%-4s %-24s %-24s %-24s" % (ch, fmt(a), fmt(b), fmt(c)))