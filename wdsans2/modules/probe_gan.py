#!/usr/bin/env python3
import sys
sys.path.insert(0, "/workspace/wdsans2/probe")
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from canonpen3 import contours_from_pen
import numpy as np

for lbl, p in (("我们","/workspace/static/wdsans/WDesignSans-VF.otf"),
               ("OPPO","/workspace/wdsans/ref/ops/ops-400.ttf")):
    f = TTFont(p, lazy=True); cm = f.getBestCmap(); gs = f.getGlyphSet()
    if ord("干") not in cm:
        print("%s 无 干" % lbl); f.close(); continue
    rp = RecordingPen(); gs[cm[ord("干")]].draw(rp); f.close()
    C = contours_from_pen(rp.value)
    print("=== %s 干  共 %d 轮廓 ===" % (lbl, len(C)))
    for i,c in enumerate(C):
        pts=[tuple(c["start"])]
        for s in c["segs"]:
            if s[0]=="L": pts.append(tuple(s[1]))
            elif s[0]=="C": pts+=[tuple(s[1]),tuple(s[2]),tuple(s[3])]
            elif s[0]=="Q": pts+=[tuple(s[1]),tuple(s[2])]
            elif s[0]=="QM":
                for q in s[1]: pts.append(tuple(q))
        xs=[q[0] for q in pts]; ys=[q[1] for q in pts]
        w=max(xs)-min(xs); h=max(ys)-min(ys)
        print("  轮廓[%d] %d段 bbox x[%.0f,%.0f] y[%.0f,%.0f] w=%.0f h=%.0f" % (
            i, len(c["segs"]), min(xs),max(xs),min(ys),max(ys),w,h))
        # 只 dump 横笔（宽>>高）
        if w > 400 and h < 200:
            print("      起点 (%.0f,%.0f)" % c["start"])
            for j,s in enumerate(c["segs"]):
                t=s[0]
                if t=="L": print("        [%d] L -> (%.0f,%.0f)" % (j,s[1][0],s[1][1]))
                elif t=="C": print("        [%d] C c1(%.0f,%.0f) c2(%.0f,%.0f) -> (%.0f,%.0f)" % (
                    j,s[1][0],s[1][1],s[2][0],s[2][1],s[3][0],s[3][1]))
                elif t=="Q": print("        [%d] Q ctrl(%.0f,%.0f) -> (%.0f,%.0f)" % (
                    j,s[1][0],s[1][1],s[2][0],s[2][1]))
    print()
