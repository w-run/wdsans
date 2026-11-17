#!/usr/bin/env python3
"""yan_trace - 追查「眼」艮部撇尖 84 单位上移来自哪个阶段"""
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
  ('R2',   B+'masters_R2/master-Regular-400.otf'),
  ('R4',   B+'masters_R4/master-Regular-400.otf'),
  ('R10',  B+'masters_R10/master-Regular-400.otf'),
  ('R15',  B+'masters_R15/master-Regular-400.otf'),
  ('R29',  B+'masters_R29/master-Regular-400.otf'),
]


def yan_pts(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    if ord("眼") not in cm:
        f.close(); return None
    rp = DecomposingRecordingPen(gs); gs[cm[ord("眼")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    # 找底部右侧的撇：y_min < 50 且 x_min > 380
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
        if len(c["segs"]) <= 6 and P[:,1].min() < 50 and P[:,0].min() > 380 and P[:,0].max() > 600:
            # 找最右上的点（撇尖）
            k = np.argmax(P[:,0] - 0.5*P[:,1])
            tip = P[np.argmax(P[:,0])]
            return (round(tip[0]), round(tip[1]), len(c["segs"]))
    return None


print('%-6s %s' % ('阶段', '撇尖坐标 (x, y) / 段数'))
for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    r = yan_pts(p)
    print("  %-6s %s" % (lbl, str(r) if r else "-"))