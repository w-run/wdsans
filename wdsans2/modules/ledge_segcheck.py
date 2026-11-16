#!/usr/bin/env python3
"""ledge_segcheck - 检查 8 个人字头字的横笔段型"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen


def endp(s):
    if s[0] == 'QM':
        return np.array(s[1][-1], float)
    return np.array(s[-1], float)


def show(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    C = contours_from_pen(rp.value)
    allP = []
    for c in C:
        P = np.array([[c["start"][0], c["start"][1]]] +
                     [[endp(s)[0], endp(s)[1]] for s in c["segs"]], float)
        allP.append(P)
    gmax = max(P[:, 1].max() for P in allP)
    gx0 = min(P[:, 0].min() for P in allP)
    gx1 = max(P[:, 0].max() for P in allP)
    print("  %-5s %d轮廓 gmax=%.0f x[%.0f,%.0f]" % (lbl, len(C), gmax, gx0, gx1))
    for ci, (c, P) in enumerate(zip(C, allP)):
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        w = x1 - x0; h = max(y1 - y0, 1)
        if w < 300 or w / h < 1.8:
            continue
        if y1 < gmax - 300:
            continue
        sig = "".join("C" if s[0]=="C" else "Q" if s[0]=="Q" else "M" if s[0]=="QM" else "L" for s in c["segs"])
        print("    c%-2d %-10s %d段 %d点 x[%4.0f,%4.0f] y[%4.0f,%4.0f]" %
              (ci, sig, len(c["segs"]), len(P), x0, x1, y0, y1))


print('=== 8 个人字头字的顶部横笔结构 ===')
for ch in '愈命盒朵俞拿舍禽':
    print("--- %s ---" % ch)
    show("/workspace/static/wdsans/WDesignSans-VF.otf", ch, "我们")
    show("/workspace/wdsans/ref/hos/hos-400.ttf", ch, "HOS")
    print()