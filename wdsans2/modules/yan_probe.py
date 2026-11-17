#!/usr/bin/env python3
"""yan_probe - 查「眼」艮部底部尖刺来自哪里"""
import sys
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

FONTS = [('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
         ('R15', '/workspace/wdsans2/build/masters_R15/master-Regular-400.otf'),
         ('R29', '/workspace/wdsans2/build/masters_R29/master-Regular-400.otf'),
         ('VF',  '/workspace/static/wdsans/WDesignSans-VF.otf'),
         ('OPPO','/workspace/wdsans/ref/ops4/OPPOSans4.ttf'),
         ('HOS', '/workspace/wdsans/ref/hos/hos-400.ttf')]


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


for lbl, p in FONTS:
    f = TTFont(p, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord("眼") not in cm:
        print("  %s 无此字" % lbl); f.close(); continue
    rp = DecomposingRecordingPen(gs); gs[cm[ord("眼")]].draw(rp)
    f.close()
    C = contours_from_pen(rp.value)
    print("【%s】%d 轮廓" % (lbl, len(C)))
    for i, c in enumerate(C):
        P = allpts(c)
        sig = "".join(s[0] for s in c["segs"])
        print("   c%d x[%4.0f,%4.0f] y[%4.0f,%4.0f]  %d%s" % (
            i, P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max(), len(c["segs"]), sig))
    print()