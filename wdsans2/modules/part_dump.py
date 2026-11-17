#!/usr/bin/env python3
"""part_dump - 导出指定字的每个轮廓 path（供海报拆笔画用）"""
import sys, json
sys.path.insert(0, '/workspace/wdsans2/probe')
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen

VF = '/workspace/static/wdsans/WDesignSans-VF.otf'
OUT = '/workspace/static/wdsans/poster/parts.json'

CHARS = "永口十中田今合"

f = TTFont(VF)
gs = f.getGlyphSet(); cm = f.getBestCmap()

def dump(ch):
    gn = cm[ord(ch)]
    rp = RecordingPen()
    gs[gn].draw(rp)
    parts = []
    start = None; segs = None
    for op, args in rp.value:
        if op == "moveTo":
            if start is not None:
                parts.append((start, segs))
            start = args[0]; segs = []
        elif op in ("lineTo","curveTo","qCurveTo"):
            segs.append((op, args))
        elif op == "closePath":
            if start is not None:
                parts.append((start, segs))
            start = None; segs = None
    if start is not None:
        parts.append((start, segs))
    out = []
    for i, (st, sg) in enumerate(parts):
        xs=[st[0]]; ys=[st[1]]
        for op, args in sg:
            for p in args:
                xs.append(p[0]); ys.append(p[1])
        d = ["M %.1f %.1f" % (st[0], st[1])]
        for op, args in sg:
            if op == "lineTo":
                d.append("L %.1f %.1f" % (args[0][0], args[0][1]))
            elif op == "curveTo":
                d.append("C %.1f %.1f %.1f %.1f %.1f %.1f" % (
                    args[0][0],args[0][1],args[1][0],args[1][1],args[2][0],args[2][1]))
            elif op == "qCurveTo":
                d.append("Q %.1f %.1f %.1f %.1f" % (
                    args[0][0],args[0][1],args[1][0],args[1][1]))
        d.append("Z")
        out.append({"i": i, "d": " ".join(d),
                    "bbox": [round(min(xs),1), round(min(ys),1), round(max(xs),1), round(max(ys),1)]})
    return out

res = {}
for ch in CHARS:
    if ord(ch) in cm:
        res[ch] = dump(ch)
        print("  %s: %d 轮廓" % (ch, len(res[ch])))
f.close()
json.dump(res, open(OUT, "w"), ensure_ascii=False)
print('saved')