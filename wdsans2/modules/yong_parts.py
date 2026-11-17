#!/usr/bin/env python3
"""yong_parts - 分解「永」的轮廓，输出每个轮廓的独立 path + bbox"""
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
import numpy as np
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
OUT = '/workspace/static/wdsans/poster/yong_parts.json'

f = TTFont(VF)
gs = f.getGlyphSet(); cm = f.getBestCmap()
gn = cm[ord("永")]
rp = RecordingPen()
gs[gn].draw(rp)
f.close()

# 每个轮廓：(起点, [(op, pts)])
parts = []
start = None; segs = None
for op, args in rp.value:
    if op == "moveTo":
        if start is not None:
            parts.append((start, segs))
        start = args[0]; segs = []
    elif op in ("lineTo", "curveTo", "qCurveTo"):
        segs.append((op, args))
    elif op == "closePath":
        if start is not None:
            parts.append((start, segs))
        start = None; segs = None
if start is not None:
    parts.append((start, segs))

print('「永」共 %d 个轮廓' % len(parts))

def allpts(start, segs):
    xs = [start[0]]; ys = [start[1]]
    for op, args in segs:
        for p in args:
            xs.append(p[0]); ys.append(p[1])
    return xs, ys

def to_d(start, segs):
    out = ["M %.1f %.1f" % (start[0], start[1])]
    for op, args in segs:
        if op == "lineTo":
            out.append("L %.1f %.1f" % (args[0][0], args[0][1]))
        elif op == "curveTo":
            out.append("C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                args[0][0],args[0][1],args[1][0],args[1][1],args[2][0],args[2][1]))
        elif op == "qCurveTo":
            out.append("Q %.1f %.1f %.1f %.1f" % (
                args[0][0],args[0][1],args[1][0],args[1][1]))
    out.append("Z")
    return " ".join(out)

res = []
for i, (start, segs) in enumerate(parts):
    xs, ys = allpts(start, segs)
    b = [round(min(xs),1), round(min(ys),1), round(max(xs),1), round(max(ys),1)]
    res.append({"i": i, "bbox": b, "d": to_d(start, segs)})
    print("  c%d  x[%4.0f,%4.0f] y[%4.0f,%4.0f]  宽%3.0f 高%3.0f  段%d" % (
        i, b[0], b[2], b[1], b[3], b[2]-b[0], b[3]-b[1], len(segs)))

json.dump(res, open(OUT, "w"), ensure_ascii=False)
print('saved')