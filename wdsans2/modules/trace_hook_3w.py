#!/usr/bin/env python3
"""trace_hook_3w - trace hook closure at 250/400/900 through stages"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

B = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS',  '/workspace/wdsans/ref/shs/shs-400.otf', None),
  ('T6',   B+'masters_T6', 'master-Regular-400.otf'),
  ('MOD',  B+'masters_MOD', 'master-Regular-400.otf'),
  ('R1',   B+'masters_R1', 'master-Regular-400.otf'),
  ('R2',   B+'masters_R2', 'master-Regular-400.otf'),
  ('R4',   B+'masters_R4', 'master-Regular-400.otf'),
  ('R10',  B+'masters_R10', 'master-Regular-400.otf'),
  ('R15',  B+'masters_R15', 'master-Regular-400.otf'),
  ('R29',  B+'masters_R29', 'master-Regular-400.otf'),
  ('R30',  B+'masters_R30', 'master-Regular-400.otf'),
]


def hook(path):
    f = TTFont(path, lazy=True); gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen(); gs[cm[ord("永")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    best = None
    for ci, c in enumerate(C):
        if len(c["segs"]) < 6:
            continue
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
        h = P[:,1].max() - P[:,1].min()
        if best is None or h > best[0]:
            best = (h, ci, c)
    if not best:
        return None
    c = best[2]
    st = np.array(c["start"], float)
    last = np.array(c["segs"][-1][-1], float)
    return (len(c["segs"]), st, last, float(np.hypot(*(last-st))))


print('%-6s %-5s %-28s %s' % ('stage','segs','start','end  gap'))
for lbl, d, fn in STAGES:
    if fn is None:
        p = d
    else:
        p = os.path.join(d, fn)
    if not os.path.exists(p):
        continue
    r = hook(p)
    if not r:
        print("  %-6s (no 6+ seg contour)" % lbl)
        continue
    n, st, last, gap = r
    print("  %-6s %-5d (%7.1f,%7.1f)      (%7.1f,%7.1f)  gap=%.1f" % (
        lbl, n, st[0], st[1], last[0], last[1], gap))