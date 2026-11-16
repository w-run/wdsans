#!/usr/bin/env python3
"""ledge_detail - 精确分析 盒俞拿禽 的顶部横笔"""
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


def detail(path, ch, lbl):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord(ch) not in cm:
        print("  %s 无此字" % lbl); f.close(); return
    rp = RecordingPen()
    gs[cm[ord(ch)]].draw(rp)
    f.close()
    C = contours_from_pen(rp.value)
    # 全字 bbox
    allx = []; ally = []
    for c in C:
        allx.append(c['start'][0]); ally.append(c['start'][1])
        for s in c['segs']:
            if s[0] == 'QM':
                for p in s[1]:
                    allx.append(p[0]); ally.append(p[1])
            elif s[0] == 'C':
                allx.extend([s[1][0], s[2][0], s[3][0]])
                ally.extend([s[1][1], s[2][1], s[3][1]])
            elif s[0] == 'Q':
                allx.extend([s[1][0], s[2][0]])
                ally.extend([s[1][1], s[2][1]])
            else:
                allx.append(s[1][0]); ally.append(s[1][1])
    gmax = max(ally); gx1 = max(allx)
    print("  %-5s %d轮廓 gmax=%.0f 右界=%.0f" % (lbl, len(C), gmax, gx1))
    # 找宽扁轮廓
    for ci, c in enumerate(C):
        P = np.array([[c["start"][0], c["start"][1]]] +
                     [[endp(s)[0], endp(s)[1]] for s in c["segs"]], float)
        x0, x1 = P[:, 0].min(), P[:, 0].max()
        y0, y1 = P[:, 1].min(), P[:, 1].max()
        w = x1 - x0; h = max(y1 - y0, 1)
        if w < 350 or w / h < 2.0:
            continue
        sig = "".join("C" if s[0]=="C" else "Q" if s[0]=="Q" else "M" if s[0]=="QM" else "L" for s in c["segs"])
        print("    c%-2d %-8s %d段 x[%4.0f,%4.0f] y[%4.0f,%4.0f] 宽%4.0f" %
              (ci, sig, len(c["segs"]), x0, x1, y0, y1, w))
        # 打印各点坐标（若点数少）
        if len(P) <= 8:
            for k, p in enumerate(P):
                print("        p%d (%.0f,%.0f)" % (k, p[0], p[1]))


for ch in '盒俞拿禽':
    print("=== %s ===" % ch)
    detail("/workspace/static/wdsans/WDesignSans-VF.otf", ch, "我们")
    detail("/workspace/wdsans/ref/hos/hos-400.ttf", ch, "HOS")
    print()