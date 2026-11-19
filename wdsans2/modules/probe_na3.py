#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen

OURS = "/workspace/static/wdsans/WDesignSans-VF.otf"
OPPO = "/workspace/wdsans/ref/ops/ops-400.ttf"

def dump(path, ch, name):
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    if ord(ch) not in cm:
        print("  无"); f.close(); return
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s %s ===" % (name, ch))
    for i, c in enumerate(C):
        # 端点列表
        pts = [tuple(c["start"])]
        for s in c["segs"]:
            if s[0] == "L": pts.append(tuple(s[1]))
            elif s[0] == "C": pts += [tuple(s[1]), tuple(s[2]), tuple(s[3])]
            elif s[0] == "Q": pts += [tuple(s[1]), tuple(s[2])]
            elif s[0] == "QM":
                for q in s[1]: pts.append(tuple(q))
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        w = max(xs)-min(xs); h = max(ys)-min(ys)
        if w < 200 or h < 200: continue
        sig = "".join(s[0] for s in c["segs"])
        print("  轮廓[%d] %d段 bbox x[%.0f,%.0f] y[%.0f,%.0f] 签名=%s" % (
            i, len(c["segs"]), min(xs), max(xs), min(ys), max(ys), sig))
        # 捺尖: x 大 y 小 -> score = x - y
        best = None
        for j, s in enumerate(c["segs"]):
            e = s[-1]
            if not (isinstance(e, tuple) and len(e)==2 and isinstance(e[0], (int,float))): continue
            sc = e[0] - e[1]
            if best is None or sc > best[0]: best = (sc, j, s)
        if best:
            _, j, s = best
            t = s[0]
            if t == "C":
                print("    捺尖端[%d] C: c1(%.0f,%.0f) c2(%.0f,%.0f) end(%.0f,%.0f)" % (
                    j, s[1][0], s[1][1], s[2][0], s[2][1], s[3][0], s[3][1]))
            elif t == "L":
                print("    捺尖端[%d] L: end(%.0f,%.0f)" % (j, s[1][0], s[1][1]))
            elif t in ("Q","QM"):
                print("    捺尖端[%d] %s: %s" % (j, t, str(s[1:])[:110]))
    print()

for ch in ("大","人","天","夫"):
    dump(OURS, ch, "我们")
    dump(OPPO, ch, "OPPO")
