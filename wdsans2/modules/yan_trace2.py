#!/usr/bin/env python3
"""yan_trace2 - 精确追踪 c4 轮廓（x[426,689] y[-80,84]）的右上尖点"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen, DecomposingRecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',   B+'masters_T6/master-Regular-400.otf'),
  ('MOD',  B+'masters_MOD/master-Regular-400.otf'),
  ('R1',   B+'masters_R1/master-Regular-400.otf'),
  ('R4',   B+'masters_R4/master-Regular-400.otf'),
  ('R15',  B+'masters_R15/master-Regular-400.otf'),
  ('R29',  B+'masters_R29/master-Regular-400.otf'),
]


def find_c4(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = DecomposingRecordingPen(gs); gs[cm[ord("眼")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    for c in C:
        pts = [np.array(c["start"], float)]
        for s in c["segs"]:
            if s[0] == "QM":
                for q in s[1]: pts.append(np.array(q, float))
            elif s[0] == "C":
                pts.extend([np.array(s[1],float), np.array(s[2],float), np.array(s[3],float)])
            elif s[0] == "Q":
                pts.extend([np.array(s[1],float), np.array(s[2],float)])
            else:
                pts.append(np.array(s[1], float))
        P = np.array(pts)
        # c4 特征: x 范围约 [420,700], y 范围约 [-90,100]
        if 400 < P[:,0].min() < 470 and 650 < P[:,0].max() < 720 and P[:,1].max() < 150:
            tip = P[np.argmax(P[:,0])]
            return (round(tip[0]), round(tip[1]), len(c["segs"]), "".join(s[0] for s in c["segs"]))
    return None


print('%-6s %s' % ('阶段', 'c4 最右点 (x,y) / 段数 / 签名'))
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    r = find_c4(p)
    print("  %-6s %s" % (lbl, str(r) if r else "(未找到 c4 形态)"))