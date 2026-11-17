#!/usr/bin/env python3
"""dao_trace - 到 的 c3 横笔逐阶段溯源"""
import sys, os
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

BASE = '/workspace/wdsans2/build/'
STAGES = [
  ('SHS', '/workspace/wdsans/ref/shs/shs-400.otf'),
  ('T6',  BASE+'masters_T6/master-Regular-400.otf'),
  ('MOD', BASE+'masters_MOD/master-Regular-400.otf'),
  ('R1',  BASE+'masters_R1/master-Regular-400.otf'),
  ('R4',  BASE+'masters_R4/master-Regular-400.otf'),
  ('R10', BASE+'masters_R10/master-Regular-400.otf'),
  ('R15', BASE+'masters_R15/master-Regular-400.otf'),
  ('R16', BASE+'masters_R16/master-Regular-400.otf'),
  ('R25b',BASE+'masters_R25b/master-Regular-400.otf'),
]


def topbars(path):
    f = TTFont(path, lazy=True)
    gs = f.getGlyphSet(); cm = f.getBestCmap()
    rp = RecordingPen()
    gs[cm[ord("到")]].draw(rp)
    f.close()
    parts = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None: parts.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None: parts.append((start, segs))
            start = None; segs = None
    if start is not None: parts.append((start, segs))
    out = []
    for i, (st, sg) in enumerate(parts):
        pts = [np.array(st, float)]
        for op, args in sg:
            for p in args: pts.append(np.array(p, float))
        P = np.array(pts)
        out.append((i, len(sg), P[:,0].min(), P[:,0].max(), P[:,1].min(), P[:,1].max()))
    return out


for lbl, p in STAGES:
    if not os.path.exists(p):
        continue
    bars = topbars(p)
    # 找 y_max > 700 的轮廓
    hi = [b for b in bars if b[5] > 700]
    print("  %-5s %d轮廓  顶部区域: %s" % (lbl, len(bars),
          " ".join("c%d(%d段,x[%.0f,%.0f],y[%.0f,%.0f])" % (b[0],b[1],b[2],b[3],b[4],b[5]) for b in hi)))