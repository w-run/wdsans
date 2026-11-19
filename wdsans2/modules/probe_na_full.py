#!/usr/bin/env python3
"""完整 dump 大 的轮廓结构，看清捺末端段的上下文"""
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

OURS = "/workspace/static/wdsans/WDesignSans-VF.otf"

def dump(path, ch, name):
    f = TTFont(path, lazy=True)
    cm = f.getBestCmap(); gs = f.getGlyphSet()
    rp = RecordingPen(); gs[cm[ord(ch)]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s %s  共 %d 个轮廓 ===" % (name, ch, len(C)))
    for i, c in enumerate(C):
        pts = [tuple(c["start"])]
        for s in c["segs"]:
            if s[0] == "L": pts.append(tuple(s[1]))
            elif s[0] == "C": pts += [tuple(s[1]), tuple(s[2]), tuple(s[3])]
            elif s[0] == "Q": pts += [tuple(s[1]), tuple(s[2])]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        w = max(xs)-min(xs); h = max(ys)-min(ys)
        if w < 150 and h < 150: continue
        print("  --- 轮廓[%d] bbox x[%.0f,%.0f] y[%.0f,%.0f] ---" % (
            i, min(xs), max(xs), min(ys), max(ys)))
        print("      起点 (%.0f,%.0f)" % c["start"])
        for j, s in enumerate(c["segs"]):
            t = s[0]
            if t == "L":
                print("      [%d] L    -> (%.0f,%.0f)" % (j, s[1][0], s[1][1]))
            elif t == "C":
                print("      [%d] C    c1(%.0f,%.0f) c2(%.0f,%.0f) -> (%.0f,%.0f)" % (
                    j, s[1][0], s[1][1], s[2][0], s[2][1], s[3][0], s[3][1]))
            elif t == "Q":
                print("      [%d] Q    ctrl(%.0f,%.0f) -> (%.0f,%.0f)" % (
                    j, s[1][0], s[1][1], s[2][0], s[2][1]))
            elif t == "QM":
                print("      [%d] QM   %s" % (j, str(s[1])[:100]))
    print()

dump(OURS, "大", "我们")
dump(OURS, "人", "我们")
